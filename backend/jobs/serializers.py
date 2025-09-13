from rest_framework import serializers
from .models import Job, JobAttempt, JobFeed
from campaigns.models import Campaign
from users.models import User


class JobSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)
    promoter_name = serializers.CharField(source='campaign.promoter.username', read_only=True)
    earner_name = serializers.CharField(source='earner.username', read_only=True)
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'campaign', 'campaign_title', 'promoter_name', 'earner', 'earner_name',
            'action_type', 'reward_amount', 'status', 'deadline', 'time_remaining',
            'created_at', 'updated_at', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_time_remaining(self, obj):
        if obj.deadline:
            from django.utils import timezone
            now = timezone.now()
            if obj.deadline > now:
                delta = obj.deadline - now
                return {
                    'hours': delta.total_seconds() // 3600,
                    'minutes': (delta.total_seconds() % 3600) // 60,
                    'total_seconds': delta.total_seconds()
                }
        return None


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'campaign', 'action_type', 'reward_amount', 'deadline', 'metadata'
        ]
    
    def validate_campaign(self, value):
        if value.status != 'active':
            raise serializers.ValidationError("Job can only be created for active campaigns")
        return value
    
    def validate_reward_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Reward amount must be greater than 0")
        return value


class JobAttemptSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.campaign.title', read_only=True)
    earner_name = serializers.CharField(source='earner.username', read_only=True)
    
    class Meta:
        model = JobAttempt
        fields = [
            'id', 'job', 'job_title', 'earner', 'earner_name', 'proof_data',
            'verification_status', 'ai_score', 'verifier_notes', 'created_at',
            'updated_at', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class JobAttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAttempt
        fields = ['job', 'proof_data', 'metadata']
    
    def validate_job(self, value):
        if value.status != 'open':
            raise serializers.ValidationError("Job is not available for attempts")
        return value
    
    def validate(self, data):
        # Check if user has already attempted this job
        existing_attempt = JobAttempt.objects.filter(
            job=data['job'],
            earner=self.context['request'].user
        ).exists()
        
        if existing_attempt:
            raise serializers.ValidationError("You have already attempted this job")
        
        return data


class JobFeedSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = JobFeed
        fields = [
            'id', 'job', 'priority_score', 'is_featured', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class JobAcceptSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    
    def validate_job_id(self, value):
        try:
            job = Job.objects.get(id=value)
            if job.status != 'open':
                raise serializers.ValidationError("Job is not available")
            if job.earner is not None:
                raise serializers.ValidationError("Job has already been accepted")
            return value
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found")


class JobSubmitSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    proof_data = serializers.JSONField()
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate_job_id(self, value):
        try:
            job = Job.objects.get(id=value)
            if job.status != 'accepted':
                raise serializers.ValidationError("Job is not in accepted status")
            return value
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found")


class JobFilterSerializer(serializers.Serializer):
    platform = serializers.CharField(required=False)
    engagement_type = serializers.CharField(required=False)
    min_reward = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_reward = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    status = serializers.CharField(required=False)
    sort_by = serializers.ChoiceField(
        choices=['reward_amount', 'created_at', 'deadline'],
        required=False,
        default='created_at'
    )
    sort_order = serializers.ChoiceField(
        choices=['asc', 'desc'],
        required=False,
        default='desc'
    )
    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)
    offset = serializers.IntegerField(required=False, default=0, min_value=0)
