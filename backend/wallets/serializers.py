from rest_framework import serializers
from .models import WalletTransaction, Withdrawal
from users.models import User


class WalletTransactionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'user', 'user_name', 'transaction_type', 'amount',
            'balance_before', 'balance_after', 'reference', 'description',
            'metadata', 'status', 'processed_at', 'payment_provider_id',
            'stripe_transfer_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']


class WithdrawalSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Withdrawal
        fields = [
            'id', 'user', 'user_name', 'amount', 'fee', 'net_amount',
            'status', 'payment_method', 'account_details', 'processed_at',
            'failure_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'processed_at']


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['amount', 'payment_method', 'account_details']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be greater than 0")
        
        # Check minimum withdrawal amount
        from django.conf import settings
        min_amount = getattr(settings, 'MIN_WITHDRAWAL_AMOUNT', 10.00)
        if value < min_amount:
            raise serializers.ValidationError(f"Minimum withdrawal amount is ${min_amount}")
        
        return value
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Check if user has sufficient balance
        if user.wallet_balance < data['amount']:
            raise serializers.ValidationError("Insufficient wallet balance")
        
        # Check if user has pending withdrawals
        pending_withdrawals = Withdrawal.objects.filter(
            user=user,
            status__in=['pending', 'processing']
        ).aggregate(total=serializers.Sum('amount'))['total'] or 0
        
        if user.wallet_balance - pending_withdrawals < data['amount']:
            raise serializers.ValidationError("Insufficient available balance (considering pending withdrawals)")
        
        # Check KYC requirements
        if data['amount'] >= 100.00 and not user.is_verified:
            raise serializers.ValidationError("KYC verification required for withdrawals over $100")
        
        return data


class WalletBalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_withdrawals = serializers.DecimalField(max_digits=10, decimal_places=2)
    available_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_withdrawn = serializers.DecimalField(max_digits=10, decimal_places=2)


class TransactionHistorySerializer(serializers.Serializer):
    transactions = WalletTransactionSerializer(many=True)
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()


class WithdrawalStatsSerializer(serializers.Serializer):
    total_withdrawals = serializers.IntegerField()
    pending_withdrawals = serializers.IntegerField()
    completed_withdrawals = serializers.IntegerField()
    failed_withdrawals = serializers.IntegerField()
    total_amount_withdrawn = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_withdrawal_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    withdrawal_success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class AdminWithdrawalSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Withdrawal
        fields = [
            'id', 'user', 'user_name', 'user_email', 'amount', 'fee', 'net_amount',
            'status', 'payment_method', 'account_details', 'processed_at',
            'failure_reason', 'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'processed_at']


class AdminWithdrawalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['status', 'admin_notes', 'failure_reason']
    
    def validate_status(self, value):
        valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value


class BulkWithdrawalSerializer(serializers.Serializer):
    withdrawal_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=50
    )
    action = serializers.ChoiceField(choices=['approve', 'reject', 'process'])
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_withdrawal_ids(self, value):
        # Check if all withdrawals exist and are in pending status
        withdrawals = Withdrawal.objects.filter(id__in=value, status='pending')
        if withdrawals.count() != len(value):
            raise serializers.ValidationError("Some withdrawals are not found or not in pending status")
        return value
