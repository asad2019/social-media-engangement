from rest_framework import serializers
from .models import (
    VerificationRule, VerificationSession, VerificationLog,
    ManualReviewQueue, FraudDetection, FraudAlert
)
from jobs.models import JobAttempt
from users.models import User


class VerificationRuleSerializer(serializers.ModelSerializer):
    """Serializer for verification rules"""
    
    class Meta:
        model = VerificationRule
        fields = [
            'id', 'name', 'platform', 'engagement_type',
            'verification_methods', 'timeout_seconds', 'retry_attempts',
            'pass_threshold', 'manual_review_threshold', 'fail_threshold',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VerificationSessionSerializer(serializers.ModelSerializer):
    """Serializer for verification sessions"""
    
    class Meta:
        model = VerificationSession
        fields = [
            'id', 'job_attempt', 'verification_rule', 'status',
            'ai_score', 'confidence', 'reasoning', 'evidence',
            'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'ai_score', 'confidence', 'reasoning', 'evidence',
            'started_at', 'completed_at', 'created_at'
        ]


class VerificationLogSerializer(serializers.ModelSerializer):
    """Serializer for verification logs"""
    
    class Meta:
        model = VerificationLog
        fields = [
            'id', 'verification_session', 'method', 'status',
            'confidence', 'execution_time_ms', 'error_message',
            'evidence', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ManualReviewQueueSerializer(serializers.ModelSerializer):
    """Serializer for manual review queue"""
    job_attempt_id = serializers.UUIDField(source='job_attempt.id', read_only=True)
    earner_username = serializers.CharField(source='job_attempt.earner.username', read_only=True)
    campaign_title = serializers.CharField(source='job_attempt.job.campaign.title', read_only=True)
    platform = serializers.CharField(source='job_attempt.job.campaign.platform', read_only=True)
    engagement_type = serializers.CharField(source='job_attempt.job.campaign.engagement_type', read_only=True)
    reward_amount = serializers.DecimalField(source='job_attempt.reward_amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ManualReviewQueue
        fields = [
            'id', 'job_attempt_id', 'earner_username', 'campaign_title',
            'platform', 'engagement_type', 'reward_amount', 'priority',
            'reason', 'evidence', 'fraud_indicators', 'status',
            'reviewed_by', 'reviewed_at', 'reviewer_notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'job_attempt_id', 'earner_username', 'campaign_title',
            'platform', 'engagement_type', 'reward_amount', 'evidence',
            'fraud_indicators', 'reviewed_by', 'reviewed_at', 'reviewer_notes', 'created_at'
        ]


class ManualReviewActionSerializer(serializers.Serializer):
    """Serializer for manual review actions"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_notes(self, value):
        """Validate notes length"""
        if len(value) > 1000:
            raise serializers.ValidationError("Notes cannot exceed 1000 characters")
        return value


class FraudDetectionSerializer(serializers.ModelSerializer):
    """Serializer for fraud detection records"""
    job_attempt_id = serializers.UUIDField(source='job_attempt.id', read_only=True)
    earner_username = serializers.CharField(source='job_attempt.earner.username', read_only=True)
    
    class Meta:
        model = FraudDetection
        fields = [
            'id', 'job_attempt_id', 'earner_username', 'fraud_score',
            'fraud_indicators', 'status', 'detected_at', 'created_at'
        ]
        read_only_fields = ['id', 'detected_at', 'created_at']


class FraudAlertSerializer(serializers.ModelSerializer):
    """Serializer for fraud alerts"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    fraud_detection_id = serializers.UUIDField(source='fraud_detection.id', read_only=True)
    
    class Meta:
        model = FraudAlert
        fields = [
            'id', 'fraud_detection_id', 'user_username', 'severity',
            'status', 'description', 'resolved_at', 'resolved_by',
            'resolution_notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'fraud_detection_id', 'user_username', 'resolved_at',
            'resolved_by', 'resolution_notes', 'created_at'
        ]


class FraudAlertResolutionSerializer(serializers.Serializer):
    """Serializer for resolving fraud alerts"""
    resolution_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_resolution_notes(self, value):
        """Validate resolution notes length"""
        if len(value) > 1000:
            raise serializers.ValidationError("Resolution notes cannot exceed 1000 characters")
        return value


class VerificationStatsSerializer(serializers.Serializer):
    """Serializer for verification statistics"""
    total_verifications = serializers.IntegerField()
    verified_count = serializers.IntegerField()
    rejected_count = serializers.IntegerField()
    manual_review_count = serializers.IntegerField()
    fraud_detected_count = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    success_rate = serializers.FloatField()


class UserFraudAnalysisSerializer(serializers.Serializer):
    """Serializer for user fraud analysis"""
    fraud_score = serializers.FloatField()
    indicators = serializers.ListField(child=serializers.CharField())
    total_attempts = serializers.IntegerField()
    success_rate = serializers.FloatField()
    platforms_used = serializers.IntegerField()


class VerificationRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating verification rules"""
    
    class Meta:
        model = VerificationRule
        fields = [
            'name', 'platform', 'engagement_type', 'verification_methods',
            'timeout_seconds', 'retry_attempts', 'pass_threshold',
            'manual_review_threshold', 'fail_threshold', 'is_active'
        ]
    
    def validate_verification_methods(self, value):
        """Validate verification methods"""
        valid_methods = ['deterministic', 'tokenized', 'screenshot', 'headless', 'manual', 'ml']
        for method in value:
            if method not in valid_methods:
                raise serializers.ValidationError(f"Invalid verification method: {method}")
        return value
    
    def validate_thresholds(self, data):
        """Validate threshold values"""
        pass_threshold = data.get('pass_threshold', 0.8)
        manual_review_threshold = data.get('manual_review_threshold', 0.6)
        fail_threshold = data.get('fail_threshold', 0.4)
        
        if not (fail_threshold <= manual_review_threshold <= pass_threshold):
            raise serializers.ValidationError(
                "Thresholds must be ordered: fail_threshold <= manual_review_threshold <= pass_threshold"
            )
        
        return data


class VerificationTestSerializer(serializers.Serializer):
    """Serializer for testing verification rules"""
    platform = serializers.CharField(max_length=20)
    engagement_type = serializers.CharField(max_length=20)
    proof_data = serializers.JSONField()
    test_methods = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    def validate_platform(self, value):
        """Validate platform"""
        valid_platforms = ['instagram', 'twitter', 'facebook', 'tiktok', 'youtube', 'linkedin', 'website']
        if value not in valid_platforms:
            raise serializers.ValidationError(f"Invalid platform: {value}")
        return value
    
    def validate_engagement_type(self, value):
        """Validate engagement type"""
        valid_types = ['like', 'follow', 'comment', 'share', 'visit', 'subscribe', 'view']
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid engagement type: {value}")
        return value
