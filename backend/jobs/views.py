from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F
from django.core.paginator import Paginator
from decimal import Decimal

from .models import Job, JobAttempt, JobFeed
from .serializers import (
    JobSerializer, JobCreateSerializer, JobAttemptSerializer, JobAttemptCreateSerializer,
    JobFeedSerializer, JobAcceptSerializer, JobSubmitSerializer, JobFilterSerializer
)
from users.permissions import IsPromoter, IsEarner, IsAdmin
from wallets.models import WalletTransaction
from verification.models import VerificationSession


class JobViewSet(viewsets.ModelViewSet):
    """ViewSet for jobs"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return JobCreateSerializer
        return JobSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Job.objects.all()
        elif user.role == 'promoter':
            return Job.objects.filter(campaign__promoter=user)
        elif user.role == 'earner':
            return Job.objects.filter(Q(status='open') | Q(earner=user))
        else:
            return Job.objects.filter(status='open')
    
    def perform_create(self, serializer):
        # Only promoters can create jobs
        if self.request.user.role != 'promoter':
            raise permissions.PermissionDenied("Only promoters can create jobs")
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsEarner])
    def accept(self, request, pk=None):
        """Accept a job"""
        job = self.get_object()
        
        if job.status != 'open':
            return Response({'error': 'Job is not available'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if job.earner is not None:
            return Response({'error': 'Job has already been accepted'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Update job
                job.earner = request.user
                job.status = 'accepted'
                job.save()
                
                # Create verification session
                VerificationSession.objects.create(
                    job_attempt=None,  # Will be updated when attempt is submitted
                    verification_methods=['deterministic', 'ml'],
                    status='pending',
                    metadata={'job_id': str(job.id), 'earner_id': str(request.user.id)}
                )
                
                return Response({'message': 'Job accepted successfully'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsEarner])
    def submit(self, request, pk=None):
        """Submit job attempt"""
        job = self.get_object()
        
        if job.earner != request.user:
            return Response({'error': 'You can only submit attempts for jobs you accepted'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if job.status != 'accepted':
            return Response({'error': 'Job is not in accepted status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if attempt already exists
        existing_attempt = JobAttempt.objects.filter(job=job, earner=request.user).exists()
        if existing_attempt:
            return Response({'error': 'You have already submitted an attempt for this job'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Create job attempt
                attempt = JobAttempt.objects.create(
                    job=job,
                    earner=request.user,
                    proof_data=request.data.get('proof_data'),
                    verification_status='pending',
                    metadata=request.data.get('metadata', {})
                )
                
                # Update job status
                job.status = 'submitted'
                job.save()
                
                # Update verification session
                verification_session = VerificationSession.objects.filter(
                    metadata__job_id=str(job.id)
                ).first()
                if verification_session:
                    verification_session.job_attempt = attempt
                    verification_session.save()
                
                return Response({'message': 'Job attempt submitted successfully', 
                               'attempt_id': attempt.id}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsPromoter])
    def approve(self, request, pk=None):
        """Approve a job attempt"""
        job = self.get_object()
        
        if job.campaign.promoter != request.user:
            return Response({'error': 'You can only approve jobs from your campaigns'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if job.status != 'submitted':
            return Response({'error': 'Job is not in submitted status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Get the job attempt
                attempt = JobAttempt.objects.filter(job=job).first()
                if not attempt:
                    return Response({'error': 'No attempt found for this job'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                # Update attempt
                attempt.verification_status = 'approved'
                attempt.verifier_notes = request.data.get('notes', '')
                attempt.save()
                
                # Update job
                job.status = 'verified'
                job.save()
                
                # Process payment
                self._process_job_payment(job, attempt)
                
                return Response({'message': 'Job approved successfully'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsPromoter])
    def reject(self, request, pk=None):
        """Reject a job attempt"""
        job = self.get_object()
        
        if job.campaign.promoter != request.user:
            return Response({'error': 'You can only reject jobs from your campaigns'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if job.status != 'submitted':
            return Response({'error': 'Job is not in submitted status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Get the job attempt
                attempt = JobAttempt.objects.filter(job=job).first()
                if not attempt:
                    return Response({'error': 'No attempt found for this job'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                # Update attempt
                attempt.verification_status = 'rejected'
                attempt.verifier_notes = request.data.get('notes', '')
                attempt.save()
                
                # Update job
                job.status = 'failed'
                job.save()
                
                return Response({'message': 'Job rejected successfully'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _process_job_payment(self, job, attempt):
        """Process payment for completed job"""
        # Credit earner
        WalletTransaction.objects.create(
            user=attempt.earner,
            transaction_type='credit',
            amount=job.reward_amount,
            balance_before=attempt.earner.wallet_balance,
            balance_after=attempt.earner.wallet_balance + job.reward_amount,
            reference=f'JOB_COMPLETION_{job.id}',
            description=f'Payment for completed job: {job.campaign.title}',
            metadata={'job_id': str(job.id), 'attempt_id': str(attempt.id)}
        )
        
        # Update earner balance
        attempt.earner.wallet_balance += job.reward_amount
        attempt.earner.save()
        
        # Debit campaign reserved funds
        campaign = job.campaign
        WalletTransaction.objects.create(
            user=campaign.promoter,
            transaction_type='debit',
            amount=job.reward_amount,
            balance_before=campaign.promoter.wallet_balance,
            balance_after=campaign.promoter.wallet_balance,
            reference=f'CAMPAIGN_SPEND_{job.id}',
            description=f'Spend for job completion: {job.campaign.title}',
            metadata={'job_id': str(job.id), 'campaign_id': str(campaign.id)}
        )
        
        # Update campaign reserved funds
        campaign.reserved_funds -= job.reward_amount
        campaign.save()


class JobAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for job attempts"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = JobAttempt.objects.all()
    serializer_class = JobAttemptSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return JobAttempt.objects.all()
        elif user.role == 'promoter':
            return JobAttempt.objects.filter(job__campaign__promoter=user)
        elif user.role == 'earner':
            return JobAttempt.objects.filter(earner=user)
        else:
            return JobAttempt.objects.none()


class JobFeedView(APIView):
    """Get job feed for earners"""
    permission_classes = [IsEarner]
    
    def get(self, request):
        serializer = JobFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = serializer.validated_data
        
        # Base queryset
        jobs = Job.objects.filter(status='open').select_related('campaign', 'campaign__promoter')
        
        # Apply filters
        if filters.get('platform'):
            jobs = jobs.filter(campaign__platform=filters['platform'])
        
        if filters.get('engagement_type'):
            jobs = jobs.filter(action_type=filters['engagement_type'])
        
        if filters.get('min_reward'):
            jobs = jobs.filter(reward_amount__gte=filters['min_reward'])
        
        if filters.get('max_reward'):
            jobs = jobs.filter(reward_amount__lte=filters['max_reward'])
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')
        
        if sort_order == 'desc':
            jobs = jobs.order_by(f'-{sort_by}')
        else:
            jobs = jobs.order_by(sort_by)
        
        # Pagination
        limit = filters.get('limit', 20)
        offset = filters.get('offset', 0)
        
        total_count = jobs.count()
        jobs = jobs[offset:offset + limit]
        
        serializer = JobSerializer(jobs, many=True)
        
        return Response({
            'jobs': serializer.data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_count
        }, status=status.HTTP_200_OK)


class MyJobsView(APIView):
    """Get user's jobs"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role == 'promoter':
            jobs = Job.objects.filter(campaign__promoter=user)
        elif user.role == 'earner':
            jobs = Job.objects.filter(earner=user)
        else:
            jobs = Job.objects.none()
        
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobStatsView(APIView):
    """Get job statistics"""
    permission_classes = [IsAdmin]
    
    def get(self, request):
        stats = {
            'total_jobs': Job.objects.count(),
            'open_jobs': Job.objects.filter(status='open').count(),
            'accepted_jobs': Job.objects.filter(status='accepted').count(),
            'submitted_jobs': Job.objects.filter(status='submitted').count(),
            'verified_jobs': Job.objects.filter(status='verified').count(),
            'failed_jobs': Job.objects.filter(status='failed').count(),
            'total_rewards': Job.objects.aggregate(Sum('reward_amount'))['reward_amount__sum'] or 0,
            'avg_reward': Job.objects.aggregate(Avg('reward_amount'))['reward_amount__avg'] or 0,
            'completion_rate': 0
        }
        
        total_jobs = stats['total_jobs']
        if total_jobs > 0:
            completed_jobs = stats['verified_jobs'] + stats['failed_jobs']
            stats['completion_rate'] = round((completed_jobs / total_jobs) * 100, 2)
        
        return Response(stats, status=status.HTTP_200_OK)