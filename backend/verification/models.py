import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class VerificationRule(models.Model):
    """
    Configurable verification rules for different platforms and engagement types.
    """
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
        ('website', 'Website'),
    ]
    
    ENGAGEMENT_TYPE_CHOICES = [
        ('like', 'Like'),
        ('follow', 'Follow'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('visit', 'Website Visit'),
        ('subscribe', 'Subscribe'),
        ('view', 'View'),
    ]
    
    VERIFICATION_METHOD_CHOICES = [
        ('deterministic', 'Deterministic Check'),
        ('tokenized', 'Tokenized Verification'),
        ('screenshot', 'Screenshot Analysis'),
        ('headless', 'Headless Browser'),
        ('manual', 'Manual Review'),
        ('ml', 'Machine Learning'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    engagement_type = models.CharField(max_length=20, choices=ENGAGEMENT_TYPE_CHOICES)
    
    # Verification configuration
    verification_methods = models.JSONField(default=list)  # Ordered list of methods to try
    timeout_seconds = models.PositiveIntegerField(default=300)  # 5 minutes default
    retry_attempts = models.PositiveIntegerField(default=3)
    
    # Scoring thresholds
    min_confidence_score = models.FloatField(default=0.8)
    auto_approve_threshold = models.FloatField(default=0.9)
    auto_reject_threshold = models.FloatField(default=0.3)
    
    # Platform-specific settings
    platform_settings = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'verification_rules'
        unique_together = ['platform', 'engagement_type']
        indexes = [
            models.Index(fields=['platform']),
            models.Index(fields=['engagement_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.platform} - {self.engagement_type})"


class VerificationSession(models.Model):
    """
    Tracks verification sessions for jobs.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_attempt = models.OneToOneField('jobs.JobAttempt', on_delete=models.CASCADE, related_name='verification_session')
    verification_rule = models.ForeignKey(VerificationRule, on_delete=models.CASCADE)
    
    # Session details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_method = models.CharField(max_length=20, blank=True)
    method_results = models.JSONField(default=dict)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    timeout_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    final_score = models.FloatField(null=True, blank=True)
    final_decision = models.CharField(max_length=20, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # ML metadata
    ml_model_version = models.CharField(max_length=50, blank=True)
    ml_features = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'verification_sessions'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['timeout_at']),
        ]
    
    def __str__(self):
        return f"Verification session for {self.job_attempt.id}"


class ManualReviewQueue(models.Model):
    """
    Queue for jobs requiring manual review.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('escalated', 'Escalated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_attempt = models.OneToOneField('jobs.JobAttempt', on_delete=models.CASCADE, related_name='manual_review')
    
    # Queue details
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reviews')
    
    # Review details
    review_notes = models.TextField(blank=True)
    decision = models.CharField(max_length=20, blank=True)  # approve, reject, escalate
    decision_reason = models.TextField(blank=True)
    
    # Timing
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Escalation
    escalated_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalated_reviews')
    escalation_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'manual_review_queue'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['queued_at']),
        ]
        ordering = ['priority', 'queued_at']
    
    def __str__(self):
        return f"Manual review for {self.job_attempt.id}"
    
    def assign(self, reviewer):
        """Assign review to a moderator"""
        self.assigned_to = reviewer
        self.status = 'in_review'
        self.started_at = timezone.now()
        self.save()
        return self
    
    def complete(self, decision, reason=''):
        """Complete the manual review"""
        self.decision = decision
        self.decision_reason = reason
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update job attempt
        self.job_attempt.manual_review(self.assigned_to, decision, reason)
        
        return self
    
    def escalate(self, escalated_to, reason=''):
        """Escalate the review"""
        self.escalated_to = escalated_to
        self.escalation_reason = reason
        self.status = 'escalated'
        self.save()
        return self


class VerificationLog(models.Model):
    """
    Detailed logs of verification attempts and results.
    """
    VERIFICATION_TYPE_CHOICES = [
        ('deterministic', 'Deterministic Check'),
        ('tokenized', 'Tokenized Verification'),
        ('screenshot', 'Screenshot Analysis'),
        ('headless', 'Headless Browser'),
        ('manual', 'Manual Review'),
        ('ml', 'Machine Learning'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification_session = models.ForeignKey(VerificationSession, on_delete=models.CASCADE, related_name='logs')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPE_CHOICES)
    
    # Request details
    request_data = models.JSONField(default=dict)
    request_timestamp = models.DateTimeField(auto_now_add=True)
    
    # Response details
    response_data = models.JSONField(default=dict)
    response_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Results
    success = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Performance
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'verification_logs'
        indexes = [
            models.Index(fields=['verification_type']),
            models.Index(fields=['success']),
            models.Index(fields=['request_timestamp']),
        ]
        ordering = ['-request_timestamp']
    
    def __str__(self):
        return f"{self.verification_type} verification for session {self.verification_session.id}"


class FraudDetection(models.Model):
    """
    Fraud detection and prevention rules.
    """
    RULE_TYPE_CHOICES = [
        ('rate_limit', 'Rate Limiting'),
        ('ip_check', 'IP Address Check'),
        ('device_fingerprint', 'Device Fingerprint'),
        ('behavioral', 'Behavioral Analysis'),
        ('account_score', 'Account Score Check'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    
    # Rule configuration
    conditions = models.JSONField(default=dict)
    threshold = models.FloatField(default=0.0)
    action = models.CharField(max_length=50, default='flag')  # flag, block, review
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fraud_detection_rules'
        indexes = [
            models.Index(fields=['rule_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class FraudAlert(models.Model):
    """
    Fraud alerts triggered by detection rules.
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fraud_rule = models.ForeignKey(FraudDetection, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fraud_alerts')
    job_attempt = models.ForeignKey('jobs.JobAttempt', on_delete=models.CASCADE, null=True, blank=True)
    
    # Alert details
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    description = models.TextField()
    evidence = models.JSONField(default=dict)
    
    # Investigation
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_fraud_alerts')
    investigation_notes = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    
    # Timing
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'fraud_alerts'
        indexes = [
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
            models.Index(fields=['triggered_at']),
        ]
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"Fraud alert for {self.user.username} - {self.severity}"