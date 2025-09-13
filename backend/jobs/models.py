import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Job(models.Model):
    """
    Individual jobs created from campaigns for earners to complete.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('accepted', 'Accepted'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('flagged', 'Flagged'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.CASCADE, related_name='jobs')
    earner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    
    # Job details
    action_type = models.CharField(max_length=20, choices=[
        ('like', 'Like'),
        ('follow', 'Follow'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('visit', 'Website Visit'),
        ('subscribe', 'Subscribe'),
        ('view', 'View'),
    ])
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Target information
    target_url = models.URLField()
    target_identifier = models.CharField(max_length=255, blank=True)
    
    # Requirements and criteria
    acceptance_criteria = models.JSONField(default=dict)
    comment_templates = models.JSONField(default=list, blank=True)
    required_account_score = models.FloatField(default=0.0)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Verification tracking
    verification_attempts = models.PositiveIntegerField(default=0)
    verification_notes = models.TextField(blank=True)
    verification_score = models.FloatField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jobs'
        indexes = [
            models.Index(fields=['campaign']),
            models.Index(fields=['earner']),
            models.Index(fields=['status']),
            models.Index(fields=['action_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job {self.id} - {self.action_type} for {self.reward_amount}"
    
    def soft_delete(self):
        """Soft delete the job"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def can_accept(self, user):
        """Check if user can accept this job"""
        return (
            self.status == 'open' and
            user.role == 'earner' and
            not self.is_deleted and
            (not self.expires_at or self.expires_at > timezone.now()) and
            user.reputation_score >= self.required_account_score
        )
    
    def accept(self, user):
        """Accept the job for a user"""
        if not self.can_accept(user):
            raise ValueError("Job cannot be accepted")
        
        self.earner = user
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        return self
    
    def can_submit(self, user):
        """Check if user can submit proof for this job"""
        return (
            self.status == 'accepted' and
            self.earner == user and
            not self.is_deleted
        )
    
    def submit(self, user, proof_data):
        """Submit proof for job completion"""
        if not self.can_submit(user):
            raise ValueError("Job cannot be submitted")
        
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
        
        # Create job attempt
        JobAttempt.objects.create(
            job=self,
            earner=user,
            proof_data=proof_data,
            verification_status='pending'
        )
        
        return self
    
    def verify(self, verification_result, notes=''):
        """Mark job as verified or failed"""
        if self.status != 'submitted':
            raise ValueError("Job must be submitted before verification")
        
        if verification_result == 'verified':
            self.status = 'verified'
            self.verified_at = timezone.now()
            
            # Credit earner's wallet
            if self.earner:
                from wallets.models import WalletTransaction
                WalletTransaction.objects.create(
                    user=self.earner,
                    transaction_type='credit',
                    amount=self.reward_amount,
                    reference=f"job_completion_{self.id}",
                    description=f"Payment for completing job {self.id}",
                    metadata={'job_id': str(self.id), 'campaign_id': str(self.campaign.id)}
                )
                
                # Update campaign stats
                self.campaign.jobs_completed += 1
                self.campaign.jobs_verified += 1
                self.campaign.save()
        
        elif verification_result == 'failed':
            self.status = 'failed'
            
            # Update campaign stats
            self.campaign.jobs_failed += 1
            self.campaign.save()
        
        elif verification_result == 'flagged':
            self.status = 'flagged'
        
        self.verification_notes = notes
        self.verification_attempts += 1
        self.save()
        
        return self


class JobAttempt(models.Model):
    """
    Individual attempts by earners to complete jobs.
    """
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('flagged', 'Flagged'),
        ('manual_review', 'Manual Review'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='attempts')
    earner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_attempts')
    
    # Proof data
    proof_data = models.JSONField()  # Screenshots, URLs, tracking tokens, etc.
    screenshot_urls = models.JSONField(default=list, blank=True)
    tracking_token = models.CharField(max_length=255, blank=True)
    comment_text = models.TextField(blank=True)
    
    # Verification results
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    ai_score = models.FloatField(null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_reasoning = models.TextField(blank=True)
    verifier_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_attempts')
    
    # Timing
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'job_attempts'
        indexes = [
            models.Index(fields=['job']),
            models.Index(fields=['earner']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['submitted_at']),
        ]
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Attempt {self.id} for Job {self.job.id}"
    
    def verify_with_ai(self, ai_result):
        """Update attempt with AI verification result"""
        self.ai_score = ai_result.get('score')
        self.ai_confidence = ai_result.get('confidence')
        self.ai_reasoning = ai_result.get('reasoning', '')
        
        # Determine verification status based on AI result
        if ai_result.get('verified', False):
            self.verification_status = 'verified'
        elif ai_result.get('flagged', False):
            self.verification_status = 'flagged'
        else:
            self.verification_status = 'failed'
        
        self.verified_at = timezone.now()
        self.save()
        
        # Update job status
        self.job.verify(self.verification_status, self.ai_reasoning)
        
        return self
    
    def manual_review(self, reviewer, decision, notes=''):
        """Process manual review decision"""
        self.verified_by = reviewer
        self.verifier_notes = notes
        self.verified_at = timezone.now()
        
        if decision == 'approve':
            self.verification_status = 'verified'
        elif decision == 'reject':
            self.verification_status = 'failed'
        else:
            self.verification_status = 'flagged'
        
        self.save()
        
        # Update job status
        self.job.verify(self.verification_status, notes)
        
        return self


class JobFeed(models.Model):
    """
    Cached job feed for efficient retrieval.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='feed_entry')
    
    # Feed-specific fields for filtering and sorting
    platform = models.CharField(max_length=20)
    action_type = models.CharField(max_length=20)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2)
    required_score = models.FloatField(default=0.0)
    priority_score = models.FloatField(default=0.0)  # Calculated for sorting
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_feed'
        indexes = [
            models.Index(fields=['platform']),
            models.Index(fields=['action_type']),
            models.Index(fields=['reward_amount']),
            models.Index(fields=['priority_score']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-priority_score', '-created_at']
    
    def __str__(self):
        return f"Feed entry for Job {self.job.id}"
    
    def calculate_priority_score(self):
        """Calculate priority score for feed sorting"""
        score = 0.0
        
        # Reward amount (higher is better)
        score += float(self.reward_amount) * 10
        
        # Job priority
        priority_multipliers = {
            'urgent': 2.0,
            'high': 1.5,
            'normal': 1.0,
            'low': 0.5,
        }
        score *= priority_multipliers.get(self.job.priority, 1.0)
        
        # Time decay (newer jobs get higher score)
        hours_old = (timezone.now() - self.created_at).total_seconds() / 3600
        time_decay = max(0.1, 1.0 - (hours_old / 24))  # Decay over 24 hours
        score *= time_decay
        
        self.priority_score = score
        self.save()
        return score