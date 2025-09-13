import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Campaign(models.Model):
    """
    Campaigns created by promoters for engagement tasks.
    """
    ENGAGEMENT_TYPE_CHOICES = [
        ('like', 'Like'),
        ('follow', 'Follow'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('visit', 'Website Visit'),
        ('subscribe', 'Subscribe'),
        ('view', 'View'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promoter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='campaigns')
    title = models.CharField(max_length=255)
    description = models.TextField()
    engagement_type = models.CharField(max_length=20, choices=ENGAGEMENT_TYPE_CHOICES)
    platform = models.CharField(max_length=20, choices=[
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
        ('website', 'Website'),
    ])
    
    # Target details
    target_url = models.URLField()
    target_identifier = models.CharField(max_length=255, blank=True)  # post ID, username, etc.
    
    # Campaign parameters
    quantity = models.PositiveIntegerField()
    price_per_action = models.DecimalField(max_digits=10, decimal_places=2)
    total_budget = models.DecimalField(max_digits=10, decimal_places=2)
    reserved_funds = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Targeting and requirements
    targeting_criteria = models.JSONField(default=dict)  # demographics, interests, etc.
    acceptance_criteria = models.JSONField(default=dict)  # specific requirements for completion
    comment_templates = models.JSONField(default=list, blank=True)  # suggested comments
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_start = models.BooleanField(default=False)
    auto_end = models.BooleanField(default=False)
    
    # Completion tracking
    jobs_created = models.PositiveIntegerField(default=0)
    jobs_completed = models.PositiveIntegerField(default=0)
    jobs_verified = models.PositiveIntegerField(default=0)
    jobs_failed = models.PositiveIntegerField(default=0)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaigns'
        indexes = [
            models.Index(fields=['promoter']),
            models.Index(fields=['status']),
            models.Index(fields=['engagement_type']),
            models.Index(fields=['platform']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.engagement_type} on {self.platform})"
    
    def soft_delete(self):
        """Soft delete the campaign"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    @property
    def total_cost(self):
        """Calculate total cost including platform commission"""
        return self.total_budget + self.platform_commission
    
    @property
    def remaining_budget(self):
        """Calculate remaining budget"""
        return self.total_budget - self.reserved_funds
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.jobs_created == 0:
            return 0
        return (self.jobs_completed / self.jobs_created) * 100
    
    @property
    def verification_rate(self):
        """Calculate verification success rate"""
        if self.jobs_completed == 0:
            return 0
        return (self.jobs_verified / self.jobs_completed) * 100
    
    def calculate_commission(self):
        """Calculate platform commission"""
        commission_rate = getattr(settings, 'PLATFORM_COMMISSION_RATE', 0.10)
        self.platform_commission = self.total_budget * Decimal(str(commission_rate))
        self.save()
        return self.platform_commission
    
    def can_fund(self):
        """Check if campaign can be funded"""
        return (
            self.status == 'draft' and
            self.total_budget > 0 and
            self.quantity > 0
        )
    
    def can_start(self):
        """Check if campaign can be started"""
        return (
            self.status in ['draft', 'paused'] and
            self.reserved_funds >= self.total_cost and
            self.start_date <= timezone.now() if self.start_date else True
        )
    
    def can_pause(self):
        """Check if campaign can be paused"""
        return self.status == 'active'
    
    def can_cancel(self):
        """Check if campaign can be cancelled"""
        return self.status in ['draft', 'active', 'paused']
    
    def fund_campaign(self, amount):
        """Fund the campaign with specified amount"""
        if not self.can_fund():
            raise ValueError("Campaign cannot be funded")
        
        self.reserved_funds += amount
        self.calculate_commission()
        
        if self.reserved_funds >= self.total_cost:
            self.status = 'active'
            if self.auto_start:
                self.start_date = timezone.now()
        
        self.save()
        return self
    
    def create_jobs(self):
        """Create individual jobs for this campaign"""
        from jobs.models import Job
        
        jobs_to_create = self.quantity - self.jobs_created
        if jobs_to_create <= 0:
            return []
        
        jobs = []
        for _ in range(jobs_to_create):
            job = Job.objects.create(
                campaign=self,
                action_type=self.engagement_type,
                reward_amount=self.price_per_action,
                target_url=self.target_url,
                target_identifier=self.target_identifier,
                acceptance_criteria=self.acceptance_criteria,
                comment_templates=self.comment_templates,
            )
            jobs.append(job)
        
        self.jobs_created = self.jobs_created + len(jobs)
        self.save()
        return jobs


class CampaignAnalytics(models.Model):
    """
    Analytics data for campaigns.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='analytics')
    
    # Performance metrics
    total_impressions = models.PositiveIntegerField(default=0)
    total_clicks = models.PositiveIntegerField(default=0)
    total_conversions = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    avg_engagement_time = models.DurationField(null=True, blank=True)
    bounce_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    
    # Quality metrics
    avg_account_score = models.FloatField(default=0.0)
    avg_verification_time = models.DurationField(null=True, blank=True)
    dispute_rate = models.FloatField(default=0.0)
    
    # Cost metrics
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost_per_action = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost_per_conversion = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'campaign_analytics'
    
    def __str__(self):
        return f"Analytics for {self.campaign.title}"
    
    def update_metrics(self):
        """Update analytics metrics based on campaign data"""
        # This would be called periodically or on significant events
        # Implementation would depend on specific metrics requirements
        pass