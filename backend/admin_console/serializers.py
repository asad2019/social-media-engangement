from rest_framework import serializers
from decimal import Decimal
from .models import (
    AdminAction, SystemConfiguration, PlatformMetrics, 
    NotificationTemplate, SupportTicket
)
from users.models import User
from campaigns.models import Campaign
from jobs.models import Job, JobAttempt
from wallets.models import Withdrawal


class AdminActionSerializer(serializers.ModelSerializer):
    """Serializer for admin actions"""
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    target_username = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminAction
        fields = [
            'id', 'admin_username', 'action_type', 'target_type', 'target_id',
            'target_description', 'description', 'metadata', 'reason',
            'bulk_count', 'bulk_targets', 'performed_at', 'ip_address'
        ]
        read_only_fields = ['id', 'performed_at']
    
    def get_target_username(self, obj):
        """Get target username if target is a user"""
        if obj.target_type == 'User' and obj.target_id:
            try:
                user = User.objects.get(id=obj.target_id)
                return user.username
            except User.DoesNotExist:
                return None
        return None


class SystemConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for system configuration"""
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'id', 'key', 'value', 'description', 'data_type',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlatformMetricsSerializer(serializers.ModelSerializer):
    """Serializer for platform metrics"""
    
    class Meta:
        model = PlatformMetrics
        fields = [
            'id', 'metric_name', 'metric_value', 'metric_type',
            'period_start', 'period_end', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'template_name', 'template_type', 'subject_template',
            'body_template', 'variables', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer for support tickets"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'user_username', 'ticket_type', 'priority', 'status',
            'subject', 'description', 'assigned_to_username', 'resolution',
            'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'resolved_at']


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer for dashboard overview data"""
    users = serializers.DictField()
    campaigns = serializers.DictField()
    jobs = serializers.DictField()
    financial = serializers.DictField()
    moderation = serializers.DictField()


class RecentActivitySerializer(serializers.Serializer):
    """Serializer for recent activity items"""
    type = serializers.CharField()
    timestamp = serializers.DateTimeField()
    description = serializers.CharField()
    severity = serializers.CharField()
    user_id = serializers.UUIDField(required=False, allow_null=True)
    campaign_id = serializers.UUIDField(required=False, allow_null=True)
    alert_id = serializers.UUIDField(required=False, allow_null=True)
    action_id = serializers.UUIDField(required=False, allow_null=True)


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health data"""
    overall_health = serializers.FloatField()
    services = serializers.DictField()
    status = serializers.CharField()


class UserSuspendSerializer(serializers.Serializer):
    """Serializer for user suspension"""
    reason = serializers.CharField(max_length=500)
    duration_days = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=365)
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        return value


class UserBanSerializer(serializers.Serializer):
    """Serializer for user banning"""
    reason = serializers.CharField(max_length=500)
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        return value


class UserVerifySerializer(serializers.Serializer):
    """Serializer for user verification"""
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class WalletAdjustSerializer(serializers.Serializer):
    """Serializer for wallet adjustment"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(max_length=500)
    
    def validate_amount(self, value):
        """Validate amount"""
        if abs(value) > Decimal('10000'):
            raise serializers.ValidationError("Amount cannot exceed $10,000")
        return value
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        return value


class CampaignPauseSerializer(serializers.Serializer):
    """Serializer for campaign pausing"""
    reason = serializers.CharField(max_length=500)
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        return value


class CampaignCancelSerializer(serializers.Serializer):
    """Serializer for campaign cancellation"""
    reason = serializers.CharField(max_length=500)
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        return value


class WithdrawalApproveSerializer(serializers.Serializer):
    """Serializer for withdrawal approval"""
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)


class WithdrawalRejectSerializer(serializers.Serializer):
    """Serializer for withdrawal rejection"""
    reason = serializers.CharField(max_length=500)
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        return value


class ConfigurationUpdateSerializer(serializers.Serializer):
    """Serializer for configuration updates"""
    key = serializers.CharField(max_length=100)
    value = serializers.CharField(max_length=1000)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_key(self, value):
        """Validate configuration key"""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Key must contain only alphanumeric characters, underscores, and hyphens")
        return value


class BulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions"""
    action_type = serializers.ChoiceField(choices=[
        'suspend_users', 'ban_users', 'verify_users', 'pause_campaigns',
        'cancel_campaigns', 'approve_withdrawals', 'reject_withdrawals'
    ])
    target_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    reason = serializers.CharField(max_length=500)
    
    def validate_target_ids(self, value):
        """Validate target IDs"""
        if len(value) > 100:
            raise serializers.ValidationError("Cannot process more than 100 items at once")
        return value
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        return value


class UserSearchSerializer(serializers.Serializer):
    """Serializer for user search"""
    query = serializers.CharField(max_length=100, required=False)
    role = serializers.ChoiceField(choices=['promoter', 'earner', 'admin', 'moderator'], required=False)
    kyc_status = serializers.ChoiceField(choices=['pending', 'verified', 'rejected', 'not_required'], required=False)
    is_active = serializers.BooleanField(required=False)
    date_joined_after = serializers.DateField(required=False)
    date_joined_before = serializers.DateField(required=False)
    min_reputation = serializers.FloatField(required=False, min_value=0, max_value=100)
    max_reputation = serializers.FloatField(required=False, min_value=0, max_value=100)
    
    def validate(self, data):
        """Validate search parameters"""
        if data.get('min_reputation') and data.get('max_reputation'):
            if data['min_reputation'] > data['max_reputation']:
                raise serializers.ValidationError("min_reputation cannot be greater than max_reputation")
        
        if data.get('date_joined_after') and data.get('date_joined_before'):
            if data['date_joined_after'] > data['date_joined_before']:
                raise serializers.ValidationError("date_joined_after cannot be after date_joined_before")
        
        return data


class CampaignSearchSerializer(serializers.Serializer):
    """Serializer for campaign search"""
    query = serializers.CharField(max_length=100, required=False)
    status = serializers.ChoiceField(choices=['draft', 'active', 'paused', 'completed', 'cancelled'], required=False)
    platform = serializers.ChoiceField(choices=['instagram', 'twitter', 'facebook', 'tiktok', 'youtube', 'linkedin'], required=False)
    engagement_type = serializers.ChoiceField(choices=['like', 'follow', 'comment', 'share', 'visit', 'subscribe', 'view'], required=False)
    min_budget = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    max_budget = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    created_after = serializers.DateField(required=False)
    created_before = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validate search parameters"""
        if data.get('min_budget') and data.get('max_budget'):
            if data['min_budget'] > data['max_budget']:
                raise serializers.ValidationError("min_budget cannot be greater than max_budget")
        
        if data.get('created_after') and data.get('created_before'):
            if data['created_after'] > data['created_before']:
                raise serializers.ValidationError("created_after cannot be after created_before")
        
        return data


class WithdrawalSearchSerializer(serializers.Serializer):
    """Serializer for withdrawal search"""
    status = serializers.ChoiceField(choices=['pending', 'processing', 'completed', 'failed', 'cancelled'], required=False)
    payment_method = serializers.ChoiceField(choices=['bank_transfer', 'paypal', 'stripe_connect', 'crypto'], required=False)
    min_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    max_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    requested_after = serializers.DateField(required=False)
    requested_before = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validate search parameters"""
        if data.get('min_amount') and data.get('max_amount'):
            if data['min_amount'] > data['max_amount']:
                raise serializers.ValidationError("min_amount cannot be greater than max_amount")
        
        if data.get('requested_after') and data.get('requested_before'):
            if data['requested_after'] > data['requested_before']:
                raise serializers.ValidationError("requested_after cannot be after requested_before")
        
        return data
