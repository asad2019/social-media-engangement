import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AdminAction(models.Model):
    """
    Log of admin actions for audit purposes.
    """
    ACTION_TYPE_CHOICES = [
        ('user_suspend', 'Suspend User'),
        ('user_ban', 'Ban User'),
        ('user_verify', 'Verify User'),
        ('campaign_pause', 'Pause Campaign'),
        ('campaign_cancel', 'Cancel Campaign'),
        ('campaign_refund', 'Refund Campaign'),
        ('job_approve', 'Approve Job'),
        ('job_reject', 'Reject Job'),
        ('withdrawal_approve', 'Approve Withdrawal'),
        ('withdrawal_reject', 'Reject Withdrawal'),
        ('wallet_adjust', 'Adjust Wallet'),
        ('system_config', 'System Configuration'),
        ('bulk_action', 'Bulk Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    
    # Target information
    target_type = models.CharField(max_length=50, blank=True)  # Model name
    target_id = models.UUIDField(null=True, blank=True)
    target_description = models.CharField(max_length=255, blank=True)
    
    # Action details
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    reason = models.TextField(blank=True)
    
    # Bulk action details
    bulk_count = models.PositiveIntegerField(default=1)
    bulk_targets = models.JSONField(default=list, blank=True)
    
    # Timing
    performed_at = models.DateTimeField(auto_now_add=True)
    
    # IP and session info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'admin_actions'
        indexes = [
            models.Index(fields=['admin']),
            models.Index(fields=['action_type']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['performed_at']),
        ]
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.action_type} by {self.admin.username}"


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings.
    """
    CONFIG_TYPE_CHOICES = [
        ('platform', 'Platform Settings'),
        ('verification', 'Verification Settings'),
        ('payment', 'Payment Settings'),
        ('security', 'Security Settings'),
        ('notification', 'Notification Settings'),
        ('feature_flag', 'Feature Flag'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, unique=True)
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPE_CHOICES)
    
    # Configuration values
    value = models.JSONField()
    description = models.TextField(blank=True)
    
    # Validation
    validation_rules = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_sensitive = models.BooleanField(default=False)  # Hide in UI
    
    # Audit
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_configs')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_configs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_configurations'
        indexes = [
            models.Index(fields=['config_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.key}: {self.value}"


class PlatformMetrics(models.Model):
    """Daily platform metrics for dashboard and analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    
    # User metrics
    total_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    verified_users = models.PositiveIntegerField(default=0)
    
    # Campaign metrics
    total_campaigns = models.PositiveIntegerField(default=0)
    active_campaigns = models.PositiveIntegerField(default=0)
    completed_campaigns = models.PositiveIntegerField(default=0)
    total_campaign_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Job metrics
    total_jobs = models.PositiveIntegerField(default=0)
    completed_jobs = models.PositiveIntegerField(default=0)
    verified_jobs = models.PositiveIntegerField(default=0)
    failed_jobs = models.PositiveIntegerField(default=0)
    flagged_jobs = models.PositiveIntegerField(default=0)
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_payouts = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    platform_commission = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    pending_withdrawals = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Quality metrics
    verification_rate = models.FloatField(default=0.0)
    dispute_rate = models.FloatField(default=0.0)
    fraud_rate = models.FloatField(default=0.0)
    avg_verification_time_minutes = models.FloatField(default=0.0)
    
    # System metrics
    api_requests = models.PositiveIntegerField(default=0)
    api_errors = models.PositiveIntegerField(default=0)
    avg_response_time_ms = models.FloatField(default=0.0)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_metrics'
        indexes = [
            models.Index(fields=['date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date}"


class NotificationTemplate(models.Model):
    """Email and notification templates for the platform"""
    TEMPLATE_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    TRIGGER_CHOICES = [
        ('user_registration', 'User Registration'),
        ('email_verification', 'Email Verification'),
        ('kyc_submitted', 'KYC Submitted'),
        ('kyc_approved', 'KYC Approved'),
        ('kyc_rejected', 'KYC Rejected'),
        ('campaign_funded', 'Campaign Funded'),
        ('campaign_completed', 'Campaign Completed'),
        ('job_accepted', 'Job Accepted'),
        ('job_verified', 'Job Verified'),
        ('job_failed', 'Job Failed'),
        ('withdrawal_requested', 'Withdrawal Requested'),
        ('withdrawal_completed', 'Withdrawal Completed'),
        ('withdrawal_failed', 'Withdrawal Failed'),
        ('account_suspended', 'Account Suspended'),
        ('account_banned', 'Account Banned'),
        ('manual_review_assigned', 'Manual Review Assigned'),
        ('fraud_alert', 'Fraud Alert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    trigger = models.CharField(max_length=50, choices=TRIGGER_CHOICES)
    
    # Template content
    subject = models.CharField(max_length=255, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    
    # Template variables
    variables = models.JSONField(default=list, blank=True)  # Available template variables
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Audit
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_templates')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        unique_together = ['template_type', 'trigger', 'is_default']
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['trigger']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class SupportTicket(models.Model):
    """Customer support tickets"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_customer', 'Waiting for Customer'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('account', 'Account Issues'),
        ('payment', 'Payment Issues'),
        ('verification', 'Verification Issues'),
        ('technical', 'Technical Issues'),
        ('billing', 'Billing Issues'),
        ('general', 'General Inquiry'),
        ('complaint', 'Complaint'),
        ('feature_request', 'Feature Request'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    
    # Ticket details
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Assignment
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    
    # Related objects
    related_campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.SET_NULL, null=True, blank=True)
    related_job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True)
    related_withdrawal = models.ForeignKey('wallets.Withdrawal', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    resolution = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'support_tickets'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['category']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"