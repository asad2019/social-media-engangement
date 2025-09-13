from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from decimal import Decimal

from .models import Campaign, CampaignAnalytics
from .serializers import (
    CampaignSerializer, CampaignCreateSerializer, CampaignUpdateSerializer,
    CampaignAnalyticsSerializer, CampaignPreviewSerializer, CostCalculatorSerializer
)
from users.permissions import IsPromoter, IsAdmin
from wallets.models import WalletTransaction
from payments.services import StripeService


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for campaigns"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Campaign.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CampaignCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CampaignUpdateSerializer
        return CampaignSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Campaign.objects.all()
        elif user.role == 'promoter':
            return Campaign.objects.filter(promoter=user)
        else:
            return Campaign.objects.filter(status='active')
    
    def perform_create(self, serializer):
        serializer.save(promoter=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsPromoter])
    def fund(self, request, pk=None):
        """Fund a campaign"""
        campaign = self.get_object()
        
        if campaign.promoter != request.user:
            return Response({'error': 'You can only fund your own campaigns'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if campaign.status != 'draft':
            return Response({'error': 'Only draft campaigns can be funded'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has sufficient balance
        user_balance = request.user.wallet_balance
        if user_balance < campaign.total_budget:
            return Response({'error': 'Insufficient wallet balance'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Create hold transaction
                WalletTransaction.objects.create(
                    user=request.user,
                    transaction_type='hold',
                    amount=campaign.total_budget,
                    balance_before=user_balance,
                    balance_after=user_balance - campaign.total_budget,
                    reference=f'CAMPAIGN_FUND_{campaign.id}',
                    description=f'Fund campaign: {campaign.title}',
                    metadata={'campaign_id': str(campaign.id)}
                )
                
                # Update campaign
                campaign.reserved_funds = campaign.total_budget
                campaign.status = 'active'
                campaign.start_date = timezone.now()
                campaign.save()
                
                # Update user balance
                request.user.wallet_balance -= campaign.total_budget
                request.user.save()
                
                return Response({'message': 'Campaign funded successfully'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsPromoter])
    def pause(self, request, pk=None):
        """Pause a campaign"""
        campaign = self.get_object()
        
        if campaign.promoter != request.user:
            return Response({'error': 'You can only pause your own campaigns'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if campaign.status != 'active':
            return Response({'error': 'Only active campaigns can be paused'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        campaign.status = 'paused'
        campaign.save()
        
        return Response({'message': 'Campaign paused successfully'}, 
                      status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsPromoter])
    def resume(self, request, pk=None):
        """Resume a campaign"""
        campaign = self.get_object()
        
        if campaign.promoter != request.user:
            return Response({'error': 'You can only resume your own campaigns'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if campaign.status != 'paused':
            return Response({'error': 'Only paused campaigns can be resumed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        campaign.status = 'active'
        campaign.save()
        
        return Response({'message': 'Campaign resumed successfully'}, 
                      status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsPromoter])
    def cancel(self, request, pk=None):
        """Cancel a campaign"""
        campaign = self.get_object()
        
        if campaign.promoter != request.user:
            return Response({'error': 'You can only cancel your own campaigns'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if campaign.status not in ['active', 'paused']:
            return Response({'error': 'Only active or paused campaigns can be cancelled'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Calculate refund amount
                completed_jobs = campaign.jobs.filter(status='verified').count()
                spent_amount = completed_jobs * campaign.price_per_action
                refund_amount = campaign.reserved_funds - spent_amount
                
                if refund_amount > 0:
                    # Create refund transaction
                    WalletTransaction.objects.create(
                        user=request.user,
                        transaction_type='refund',
                        amount=refund_amount,
                        balance_before=request.user.wallet_balance,
                        balance_after=request.user.wallet_balance + refund_amount,
                        reference=f'CAMPAIGN_CANCEL_{campaign.id}',
                        description=f'Refund for cancelled campaign: {campaign.title}',
                        metadata={'campaign_id': str(campaign.id), 'refund_amount': str(refund_amount)}
                    )
                    
                    # Update user balance
                    request.user.wallet_balance += refund_amount
                    request.user.save()
                
                # Update campaign
                campaign.status = 'cancelled'
                campaign.reserved_funds = 0
                campaign.save()
                
                return Response({'message': 'Campaign cancelled successfully', 
                               'refund_amount': refund_amount}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], permission_classes=[IsPromoter])
    def analytics(self, request, pk=None):
        """Get campaign analytics"""
        campaign = self.get_object()
        
        if campaign.promoter != request.user:
            return Response({'error': 'You can only view analytics for your own campaigns'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        analytics_data = {
            'campaign_id': campaign.id,
            'title': campaign.title,
            'status': campaign.status,
            'total_budget': campaign.total_budget,
            'reserved_funds': campaign.reserved_funds,
            'remaining_budget': campaign.total_budget - campaign.reserved_funds,
            'total_jobs': campaign.jobs.count(),
            'completed_jobs': campaign.jobs.filter(status='verified').count(),
            'pending_jobs': campaign.jobs.filter(status='submitted').count(),
            'failed_jobs': campaign.jobs.filter(status='failed').count(),
            'success_rate': 0,
            'cost_per_engagement': campaign.price_per_action,
            'total_spent': campaign.jobs.filter(status='verified').count() * campaign.price_per_action,
            'created_at': campaign.created_at,
            'start_date': campaign.start_date,
            'end_date': campaign.end_date
        }
        
        if analytics_data['total_jobs'] > 0:
            analytics_data['success_rate'] = round(
                (analytics_data['completed_jobs'] / analytics_data['total_jobs']) * 100, 2
            )
        
        return Response(analytics_data, status=status.HTTP_200_OK)


class CampaignAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for campaign analytics"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = CampaignAnalytics.objects.all()
    serializer_class = CampaignAnalyticsSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CampaignAnalytics.objects.all()
        elif user.role == 'promoter':
            return CampaignAnalytics.objects.filter(campaign__promoter=user)
        else:
            return CampaignAnalytics.objects.none()


class CampaignPreviewView(APIView):
    """Preview campaign cost and details"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CampaignPreviewSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CostCalculatorView(APIView):
    """Calculate campaign costs"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CostCalculatorSerializer(data=request.data)
        if serializer.is_valid():
            cost_data = serializer.calculate_cost()
            return Response(cost_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CampaignSearchView(APIView):
    """Search campaigns"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        platform = request.query_params.get('platform', '')
        engagement_type = request.query_params.get('engagement_type', '')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        campaigns = Campaign.objects.filter(status='active')
        
        if query:
            campaigns = campaigns.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        
        if platform:
            campaigns = campaigns.filter(platform=platform)
        
        if engagement_type:
            campaigns = campaigns.filter(engagement_type=engagement_type)
        
        if min_price:
            campaigns = campaigns.filter(price_per_action__gte=Decimal(min_price))
        
        if max_price:
            campaigns = campaigns.filter(price_per_action__lte=Decimal(max_price))
        
        serializer = CampaignSerializer(campaigns, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CampaignStatsView(APIView):
    """Get platform-wide campaign statistics"""
    permission_classes = [IsAdmin]
    
    def get(self, request):
        stats = {
            'total_campaigns': Campaign.objects.count(),
            'active_campaigns': Campaign.objects.filter(status='active').count(),
            'paused_campaigns': Campaign.objects.filter(status='paused').count(),
            'completed_campaigns': Campaign.objects.filter(status='completed').count(),
            'cancelled_campaigns': Campaign.objects.filter(status='cancelled').count(),
            'total_budget': Campaign.objects.aggregate(Sum('total_budget'))['total_budget__sum'] or 0,
            'reserved_funds': Campaign.objects.aggregate(Sum('reserved_funds'))['reserved_funds__sum'] or 0,
            'platforms': Campaign.objects.values('platform').annotate(count=Count('platform')),
            'engagement_types': Campaign.objects.values('engagement_type').annotate(count=Count('engagement_type')),
            'avg_campaign_value': Campaign.objects.aggregate(Avg('total_budget'))['total_budget__avg'] or 0
        }
        
        return Response(stats, status=status.HTTP_200_OK)