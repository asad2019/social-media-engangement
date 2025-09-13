import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver


class SecurityEvent(models.Model):
    """Log of security-related events for audit and monitoring."""
    
    EVENT_TYPE_CHOICES = [
        ('login_success', 'Successful Login'),
        ('login_failed', 'Failed Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('api_access', 'API Access'),
        ('data_access', 'Data Access'),
        ('data_modification', 'Data Modification'),
        ('admin_action', 'Admin Action'),
        ('payment_event', 'Payment Event'),
        ('verification_event', 'Verification Event'),
        ('fraud_detection', 'Fraud Detection'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='security_events'
    )
    
    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField()
    
    # Context information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict)
    risk_score = models.FloatField(default=0.0)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'security_events'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['event_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} - {self.user.username if self.user else 'Anonymous'}"


class AuditLog(models.Model):
    """Comprehensive audit log for all data modifications."""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('soft_delete', 'Soft Delete'),
        ('restore', 'Restore'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('permission_change', 'Permission Change'),
        ('role_change', 'Role Change'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs'
    )
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255)
    object_repr = models.CharField(max_length=255)
    
    # Change details
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
            models.Index(fields=['object_id']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} {self.model_name} - {self.object_repr}"


# Signal handlers for automatic logging
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login"""
    SecurityEvent.objects.create(
        user=user,
        event_type='login_success',
        severity='low',
        description=f"User {user.username} logged in successfully",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        request_path=request.path,
        request_method=request.method,
        metadata={
            'login_time': timezone.now().isoformat(),
            'session_key': request.session.session_key
        }
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log failed user login"""
    username = credentials.get('username', 'unknown')
    
    SecurityEvent.objects.create(
        user=None,
        event_type='login_failed',
        severity='medium',
        description=f"Failed login attempt for username: {username}",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        request_path=request.path,
        request_method=request.method,
        metadata={
            'attempted_username': username,
            'failure_time': timezone.now().isoformat()
        }
    )