import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class StripeAccount(models.Model):
    """
    Stripe Connect accounts for users (promoters and earners).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('restricted', 'Restricted'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stripe_account')
    
    # Stripe Connect account details
    stripe_account_id = models.CharField(max_length=255, unique=True)  # Stripe Connect account ID
    account_type = models.CharField(max_length=20, default='express')  # express, standard, custom
    
    # Account status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    charges_enabled = models.BooleanField(default=False)
    payouts_enabled = models.BooleanField(default=False)
    
    # KYC and verification
    details_submitted = models.BooleanField(default=False)
    requirements = models.JSONField(default=dict)  # Stripe requirements
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stripe_accounts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['stripe_account_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Stripe Account {self.stripe_account_id} for {self.user.username}"
    
    def is_fully_setup(self):
        """Check if account is fully set up for payments"""
        return (
            self.status == 'active' and
            self.charges_enabled and
            self.payouts_enabled and
            self.details_submitted
        )


class PaymentIntent(models.Model):
    """
    Stripe Payment Intents for campaign funding and other payments.
    """
    STATUS_CHOICES = [
        ('requires_payment_method', 'Requires Payment Method'),
        ('requires_confirmation', 'Requires Confirmation'),
        ('requires_action', 'Requires Action'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('requires_capture', 'Requires Capture'),
        ('canceled', 'Canceled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_intents')
    
    # Stripe details
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_client_secret = models.CharField(max_length=255, blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    description = models.TextField()
    
    # Status and metadata
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    metadata = models.JSONField(default=dict)
    
    # Reference to related objects
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_intents')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    succeeded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_intents'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status']),
            models.Index(fields=['campaign']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment Intent {self.stripe_payment_intent_id} - {self.amount} {self.currency}"
    
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'succeeded'
    
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return self.status == 'succeeded' and self.succeeded_at is not None


class Payout(models.Model):
    """
    Stripe Payouts for user withdrawals.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stripe_payouts')
    withdrawal = models.OneToOneField('wallets.Withdrawal', on_delete=models.CASCADE, related_name='stripe_payout')
    
    # Stripe details
    stripe_payout_id = models.CharField(max_length=255, unique=True)
    
    # Payout details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    arrival_date = models.DateTimeField(null=True, blank=True)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    failure_code = models.CharField(max_length=100, blank=True)
    failure_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stripe_payouts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['stripe_payout_id']),
            models.Index(fields=['status']),
            models.Index(fields=['withdrawal']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payout {self.stripe_payout_id} - {self.amount} {self.currency}"
    
    def is_successful(self):
        """Check if payout was successful"""
        return self.status == 'paid'
    
    def is_failed(self):
        """Check if payout failed"""
        return self.status == 'failed'


class Transfer(models.Model):
    """
    Stripe Transfers for moving money between accounts (e.g., platform fees).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Stripe details
    stripe_transfer_id = models.CharField(max_length=255, unique=True)
    
    # Transfer details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    destination_account = models.CharField(max_length=255)  # Stripe account ID
    
    # Reference and metadata
    reference = models.CharField(max_length=255)  # Job ID, campaign ID, etc.
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stripe_transfers'
        indexes = [
            models.Index(fields=['stripe_transfer_id']),
            models.Index(fields=['status']),
            models.Index(fields=['reference']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transfer {self.stripe_transfer_id} - {self.amount} {self.currency}"


class WebhookEvent(models.Model):
    """
    Store Stripe webhook events for audit and debugging.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Stripe event details
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    
    # Event data
    data = models.JSONField()
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'stripe_webhook_events'
        indexes = [
            models.Index(fields=['stripe_event_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['processed']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Webhook Event {self.stripe_event_id} - {self.event_type}"
    
    def mark_processed(self, error=None):
        """Mark event as processed"""
        self.processed = True
        self.processed_at = timezone.now()
        if error:
            self.processing_error = str(error)
        self.save()