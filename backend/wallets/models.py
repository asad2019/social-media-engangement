import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class WalletTransaction(models.Model):
    """
    Ledger-first wallet transaction system - the source of truth for all financial operations.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('hold', 'Hold'),
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('fee', 'Fee'),
        ('refund', 'Refund'),
        ('withdrawal', 'Withdrawal'),
        ('commission', 'Commission'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Reference and metadata
    reference = models.CharField(max_length=255)  # External reference (payment ID, job ID, etc.)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # External references
    payment_provider_id = models.CharField(max_length=255, blank=True)  # Stripe payment intent ID
    stripe_transfer_id = models.CharField(max_length=255, blank=True)  # Stripe transfer ID
    
    # Soft delete (for audit purposes, transactions should rarely be deleted)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wallet_transactions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['processed_at']),
            models.Index(fields=['is_deleted']),
        ]
        ordering = ['-processed_at']
    
    def __str__(self):
        return f"{self.transaction_type} {self.amount} for {self.user.username}"
    
    def soft_delete(self):
        """Soft delete the transaction (rarely used)"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    @classmethod
    def create_transaction(cls, user, transaction_type, amount, reference, description, metadata=None):
        """Create a new wallet transaction and update user balance"""
        with models.transaction.atomic():
            # Lock user row to prevent race conditions
            user = settings.AUTH_USER_MODEL.objects.select_for_update().get(id=user.id)
            
            balance_before = user.wallet_balance
            balance_after = balance_before + amount
            
            # Validate balance doesn't go negative
            if balance_after < 0:
                raise ValueError("Insufficient wallet balance")
            
            # Create transaction
            transaction = cls.objects.create(
                user=user,
                transaction_type=transaction_type,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                reference=reference,
                description=description,
                metadata=metadata or {}
            )
            
            # Update user balance
            user.wallet_balance = balance_after
            user.save()
            
            return transaction


class Withdrawal(models.Model):
    """
    Withdrawal requests from users.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe_connect', 'Stripe Connect'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    
    # Withdrawal details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)  # amount - fee
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Payment details
    payment_details = models.JSONField(default=dict)  # Bank account, PayPal email, etc.
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # External references
    payment_provider_id = models.CharField(max_length=255, blank=True)  # Stripe payout ID
    transaction_id = models.CharField(max_length=255, blank=True)  # External transaction ID
    
    # Admin fields
    admin_notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdrawals')
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'withdrawals'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['requested_at']),
            models.Index(fields=['is_deleted']),
        ]
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Withdrawal {self.amount} by {self.user.username}"
    
    def soft_delete(self):
        """Soft delete the withdrawal"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def can_process(self):
        """Check if withdrawal can be processed"""
        return (
            self.status == 'pending' and
            self.user.wallet_balance >= self.amount and
            self.user.can_withdraw()
        )
    
    def process(self, admin_user):
        """Process the withdrawal"""
        if not self.can_process():
            raise ValueError("Withdrawal cannot be processed")
        
        with models.transaction.atomic():
            # Lock user row
            user = settings.AUTH_USER_MODEL.objects.select_for_update().get(id=self.user.id)
            
            # Create debit transaction
            WalletTransaction.create_transaction(
                user=user,
                transaction_type='debit',
                amount=-self.amount,  # Negative amount for debit
                reference=f"withdrawal_{self.id}",
                description=f"Withdrawal request {self.id}",
                metadata={
                    'withdrawal_id': str(self.id),
                    'payment_method': self.payment_method,
                    'fee': str(self.fee)
                }
            )
            
            # Update withdrawal status
            self.status = 'processing'
            self.processed_at = timezone.now()
            self.processed_by = admin_user
            self.save()
        
        return self
    
    def complete(self, payment_provider_id=None, transaction_id=None):
        """Mark withdrawal as completed"""
        if self.status != 'processing':
            raise ValueError("Withdrawal must be processing to complete")
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.payment_provider_id = payment_provider_id or ''
        self.transaction_id = transaction_id or ''
        self.save()
        
        return self
    
    def fail(self, reason=''):
        """Mark withdrawal as failed"""
        if self.status not in ['pending', 'processing']:
            raise ValueError("Withdrawal must be pending or processing to fail")
        
        self.status = 'failed'
        self.admin_notes = reason
        self.save()
        
        # Refund the amount back to user's wallet
        WalletTransaction.create_transaction(
            user=self.user,
            transaction_type='refund',
            amount=self.amount,
            reference=f"withdrawal_refund_{self.id}",
            description=f"Refund for failed withdrawal {self.id}",
            metadata={'withdrawal_id': str(self.id), 'reason': reason}
        )
        
        return self