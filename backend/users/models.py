import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with role-based access control and platform-specific fields.
    """
    ROLE_CHOICES = [
        ('promoter', 'Promoter'),
        ('earner', 'Earner'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    ]
    
    KYC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('not_required', 'Not Required'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='earner')
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='not_required')
    reputation_score = models.FloatField(default=0.0)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # KYC fields
    first_name_kyc = models.CharField(max_length=100, blank=True)
    last_name_kyc = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    id_document_url = models.URLField(blank=True)
    id_document_type = models.CharField(max_length=50, blank=True)
    
    # Platform-specific fields
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    notification_preferences = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['kyc_status']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def soft_delete(self):
        """Soft delete the user"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft-deleted user"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    
    @property
    def full_name_kyc(self):
        """Return full name from KYC data"""
        if self.first_name_kyc and self.last_name_kyc:
            return f"{self.first_name_kyc} {self.last_name_kyc}"
        return self.get_full_name()
    
    def can_withdraw(self):
        """Check if user can withdraw based on KYC status and thresholds"""
        from django.conf import settings
        return (
            self.kyc_status == 'verified' or 
            self.wallet_balance < settings.KYC_REQUIRED_THRESHOLD
        )


class SocialAccount(models.Model):
    """
    Social media accounts linked to users for verification and job completion.
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
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    account_identifier = models.CharField(max_length=255)  # username, handle, URL, etc.
    display_name = models.CharField(max_length=255, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    account_score = models.FloatField(default=0.0)
    
    # OAuth fields
    oauth_token = models.TextField(blank=True)
    oauth_token_secret = models.TextField(blank=True)
    oauth_refresh_token = models.TextField(blank=True)
    oauth_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Account metadata
    follower_count = models.IntegerField(null=True, blank=True)
    following_count = models.IntegerField(null=True, blank=True)
    post_count = models.IntegerField(null=True, blank=True)
    account_age_days = models.IntegerField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    profile_picture_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    
    # Verification metadata
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_accounts')
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_accounts'
        unique_together = ['user', 'platform', 'account_identifier']
        indexes = [
            models.Index(fields=['platform']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['account_score']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.platform}: {self.account_identifier}"
    
    def soft_delete(self):
        """Soft delete the social account"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def calculate_account_score(self):
        """Calculate account quality score based on various metrics"""
        score = 0.0
        
        # Follower count score (logarithmic)
        if self.follower_count:
            if self.follower_count >= 10000:
                score += 30
            elif self.follower_count >= 1000:
                score += 20
            elif self.follower_count >= 100:
                score += 10
            elif self.follower_count >= 10:
                score += 5
        
        # Account age score
        if self.account_age_days:
            if self.account_age_days >= 365:
                score += 20
            elif self.account_age_days >= 180:
                score += 15
            elif self.account_age_days >= 90:
                score += 10
            elif self.account_age_days >= 30:
                score += 5
        
        # Activity score
        if self.last_activity:
            days_since_activity = (timezone.now() - self.last_activity).days
            if days_since_activity <= 7:
                score += 15
            elif days_since_activity <= 30:
                score += 10
            elif days_since_activity <= 90:
                score += 5
        
        # Profile completeness
        if self.bio:
            score += 5
        if self.profile_picture_url:
            score += 5
        
        # Follow ratio (if available)
        if self.follower_count and self.following_count:
            ratio = self.follower_count / self.following_count if self.following_count > 0 else 0
            if 0.5 <= ratio <= 2.0:  # Healthy ratio
                score += 10
            elif ratio > 2.0:  # High follower ratio
                score += 15
        
        self.account_score = min(score, 100.0)  # Cap at 100
        self.save()
        return self.account_score


class AuditLog(models.Model):
    """
    Immutable audit log for critical operations.
    """
    ACTION_CHOICES = [
        ('user_create', 'User Created'),
        ('user_update', 'User Updated'),
        ('user_delete', 'User Deleted'),
        ('account_attach', 'Social Account Attached'),
        ('account_verify', 'Social Account Verified'),
        ('campaign_create', 'Campaign Created'),
        ('campaign_fund', 'Campaign Funded'),
        ('campaign_pause', 'Campaign Paused'),
        ('campaign_cancel', 'Campaign Cancelled'),
        ('job_create', 'Job Created'),
        ('job_accept', 'Job Accepted'),
        ('job_submit', 'Job Submitted'),
        ('job_verify', 'Job Verified'),
        ('job_reject', 'Job Rejected'),
        ('wallet_credit', 'Wallet Credited'),
        ('wallet_debit', 'Wallet Debited'),
        ('withdrawal_request', 'Withdrawal Requested'),
        ('withdrawal_process', 'Withdrawal Processed'),
        ('admin_action', 'Admin Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50, blank=True)  # Model name
    target_id = models.UUIDField(null=True, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['actor']),
            models.Index(fields=['action']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} by {self.actor} at {self.created_at}"