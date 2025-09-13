from rest_framework import serializers
from decimal import Decimal
from .models import StripeAccount, PaymentIntent, Payout, Transfer, WebhookEvent


class StripeAccountSerializer(serializers.ModelSerializer):
    """Serializer for Stripe Connect accounts"""
    
    class Meta:
        model = StripeAccount
        fields = [
            'id', 'stripe_account_id', 'account_type', 'status',
            'charges_enabled', 'payouts_enabled', 'details_submitted',
            'requirements', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'stripe_account_id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Custom representation to include computed fields"""
        data = super().to_representation(instance)
        data['is_fully_setup'] = instance.is_fully_setup()
        return data


class StripeAccountCreateSerializer(serializers.Serializer):
    """Serializer for creating Stripe Connect accounts"""
    account_type = serializers.ChoiceField(
        choices=['express', 'standard', 'custom'],
        default='express'
    )
    
    def create(self, validated_data):
        """Create a new Stripe Connect account"""
        from .services import StripeService
        
        user = self.context['request'].user
        stripe_service = StripeService()
        
        return stripe_service.create_connect_account(
            user=user,
            account_type=validated_data['account_type']
        )


class AccountLinkSerializer(serializers.Serializer):
    """Serializer for creating account links"""
    refresh_url = serializers.URLField()
    return_url = serializers.URLField()
    
    def create(self, validated_data):
        """Create an account link"""
        from .services import StripeService
        
        stripe_account = self.context['stripe_account']
        stripe_service = StripeService()
        
        url = stripe_service.create_account_link(
            stripe_account=stripe_account,
            refresh_url=validated_data['refresh_url'],
            return_url=validated_data['return_url']
        )
        
        return {'url': url}


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Serializer for payment intents"""
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'stripe_payment_intent_id', 'stripe_client_secret',
            'amount', 'currency', 'description', 'status', 'metadata',
            'campaign', 'created_at', 'updated_at', 'succeeded_at'
        ]
        read_only_fields = [
            'id', 'stripe_payment_intent_id', 'stripe_client_secret',
            'status', 'created_at', 'updated_at', 'succeeded_at'
        ]
    
    def to_representation(self, instance):
        """Custom representation to include computed fields"""
        data = super().to_representation(instance)
        data['is_successful'] = instance.is_successful()
        data['can_be_refunded'] = instance.can_be_refunded()
        return data


class PaymentIntentCreateSerializer(serializers.Serializer):
    """Serializer for creating payment intents"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.50'))
    currency = serializers.CharField(max_length=3, default='usd')
    description = serializers.CharField(max_length=500)
    campaign_id = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate_amount(self, value):
        """Validate amount"""
        if value < Decimal('0.50'):
            raise serializers.ValidationError("Minimum amount is $0.50")
        return value
    
    def validate_campaign_id(self, value):
        """Validate campaign exists and belongs to user"""
        if value:
            from campaigns.models import Campaign
            try:
                campaign = Campaign.objects.get(id=value, promoter=self.context['request'].user)
                return value
            except Campaign.DoesNotExist:
                raise serializers.ValidationError("Campaign not found or access denied")
        return value
    
    def create(self, validated_data):
        """Create a new payment intent"""
        from .services import StripeService
        from campaigns.models import Campaign
        
        user = self.context['request'].user
        stripe_service = StripeService()
        
        campaign = None
        if validated_data.get('campaign_id'):
            campaign = Campaign.objects.get(id=validated_data['campaign_id'])
        
        return stripe_service.create_payment_intent(
            user=user,
            amount=validated_data['amount'],
            currency=validated_data['currency'],
            description=validated_data['description'],
            campaign=campaign,
            metadata=validated_data.get('metadata', {})
        )


class PaymentIntentConfirmSerializer(serializers.Serializer):
    """Serializer for confirming payment intents"""
    payment_intent_id = serializers.CharField(max_length=255)
    
    def validate_payment_intent_id(self, value):
        """Validate payment intent exists and belongs to user"""
        try:
            payment_intent = PaymentIntent.objects.get(
                stripe_payment_intent_id=value,
                user=self.context['request'].user
            )
            return value
        except PaymentIntent.DoesNotExist:
            raise serializers.ValidationError("Payment intent not found or access denied")
    
    def create(self, validated_data):
        """Confirm payment intent"""
        from .services import StripeService
        
        stripe_service = StripeService()
        
        return stripe_service.confirm_payment_intent(
            payment_intent_id=validated_data['payment_intent_id']
        )


class PayoutSerializer(serializers.ModelSerializer):
    """Serializer for payouts"""
    
    class Meta:
        model = Payout
        fields = [
            'id', 'stripe_payout_id', 'amount', 'currency',
            'arrival_date', 'status', 'failure_code', 'failure_message',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stripe_payout_id', 'arrival_date', 'status',
            'failure_code', 'failure_message', 'created_at', 'updated_at'
        ]
    
    def to_representation(self, instance):
        """Custom representation to include computed fields"""
        data = super().to_representation(instance)
        data['is_successful'] = instance.is_successful()
        data['is_failed'] = instance.is_failed()
        return data


class PayoutCreateSerializer(serializers.Serializer):
    """Serializer for creating payouts"""
    withdrawal_id = serializers.UUIDField()
    
    def validate_withdrawal_id(self, value):
        """Validate withdrawal exists and belongs to user"""
        from wallets.models import Withdrawal
        try:
            withdrawal = Withdrawal.objects.get(
                id=value,
                user=self.context['request'].user,
                status='pending'
            )
            return value
        except Withdrawal.DoesNotExist:
            raise serializers.ValidationError("Withdrawal not found or not pending")
    
    def create(self, validated_data):
        """Create a payout"""
        from .services import StripeService
        from wallets.models import Withdrawal
        
        stripe_service = StripeService()
        withdrawal = Withdrawal.objects.get(id=validated_data['withdrawal_id'])
        
        return stripe_service.create_payout(withdrawal)


class TransferSerializer(serializers.ModelSerializer):
    """Serializer for transfers"""
    
    class Meta:
        model = Transfer
        fields = [
            'id', 'stripe_transfer_id', 'amount', 'currency',
            'destination_account', 'reference', 'description',
            'status', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stripe_transfer_id', 'status', 'created_at', 'updated_at'
        ]


class TransferCreateSerializer(serializers.Serializer):
    """Serializer for creating transfers"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    destination_account = serializers.CharField(max_length=255)
    reference = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=500)
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate_destination_account(self, value):
        """Validate destination account exists"""
        try:
            StripeAccount.objects.get(stripe_account_id=value)
            return value
        except StripeAccount.DoesNotExist:
            raise serializers.ValidationError("Destination account not found")
    
    def create(self, validated_data):
        """Create a transfer"""
        from .services import StripeService
        
        stripe_service = StripeService()
        
        return stripe_service.create_transfer(
            amount=validated_data['amount'],
            destination_account=validated_data['destination_account'],
            reference=validated_data['reference'],
            description=validated_data['description'],
            metadata=validated_data.get('metadata', {})
        )


class RefundSerializer(serializers.Serializer):
    """Serializer for refunds"""
    payment_intent_id = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, 
        min_value=Decimal('0.01'), 
        required=False, allow_null=True
    )
    
    def validate_payment_intent_id(self, value):
        """Validate payment intent exists and belongs to user"""
        try:
            payment_intent = PaymentIntent.objects.get(
                stripe_payment_intent_id=value,
                user=self.context['request'].user
            )
            if not payment_intent.can_be_refunded():
                raise serializers.ValidationError("Payment intent cannot be refunded")
            return value
        except PaymentIntent.DoesNotExist:
            raise serializers.ValidationError("Payment intent not found or access denied")
    
    def create(self, validated_data):
        """Create a refund"""
        from .services import StripeService
        
        stripe_service = StripeService()
        
        return stripe_service.refund_payment_intent(
            payment_intent_id=validated_data['payment_intent_id'],
            amount=validated_data.get('amount')
        )


class AccountBalanceSerializer(serializers.Serializer):
    """Serializer for account balance"""
    available = serializers.ListField(
        child=serializers.DictField()
    )
    pending = serializers.ListField(
        child=serializers.DictField()
    )


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for webhook events (admin only)"""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'stripe_event_id', 'event_type', 'data',
            'processed', 'processing_error', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'stripe_event_id', 'event_type', 'data',
            'processed', 'processing_error', 'created_at', 'processed_at'
        ]