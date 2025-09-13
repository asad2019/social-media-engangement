from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    AdminAction, SystemConfiguration, PlatformMetrics,
    NotificationTemplate, SupportTicket
)
from .serializers import (
    AdminActionSerializer, SystemConfigurationSerializer, PlatformMetricsSerializer,
    NotificationTemplateSerializer, SupportTicketSerializer,
    DashboardOverviewSerializer, RecentActivitySerializer, SystemHealthSerializer,
    UserSuspendSerializer, UserBanSerializer, UserVerifySerializer, WalletAdjustSerializer,
    CampaignPauseSerializer, CampaignCancelSerializer,
    WithdrawalApproveSerializer, WithdrawalRejectSerializer,
    ConfigurationUpdateSerializer, BulkActionSerializer,
    UserSearchSerializer, CampaignSearchSerializer, WithdrawalSearchSerializer
)
from .services import (
    AdminDashboardService, UserManagementService, CampaignManagementService,
    FinancialManagementService, SystemConfigurationService
)
from users.models import User
from campaigns.models import Campaign
from wallets.models import Withdrawal


class AdminActionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for admin actions (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = AdminAction.objects.all()
    serializer_class = AdminActionSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access admin actions
        if self.request.user.role in ['admin', 'moderator']:
            return AdminAction.objects.all()
        return AdminAction.objects.none()


class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for system configuration (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    
    def get_queryset(self):
        # Only admins can access system configuration
        if self.request.user.role == 'admin':
            return SystemConfiguration.objects.all()
        return SystemConfiguration.objects.none()


class PlatformMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for platform metrics (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = PlatformMetrics.objects.all()
    serializer_class = PlatformMetricsSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access platform metrics
        if self.request.user.role in ['admin', 'moderator']:
            return PlatformMetrics.objects.all()
        return PlatformMetrics.objects.none()


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for notification templates (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    
    def get_queryset(self):
        # Only admins can access notification templates
        if self.request.user.role == 'admin':
            return NotificationTemplate.objects.all()
        return NotificationTemplate.objects.none()


class SupportTicketViewSet(viewsets.ModelViewSet):
    """ViewSet for support tickets (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access support tickets
        if self.request.user.role in ['admin', 'moderator']:
            return SupportTicket.objects.all()
        return SupportTicket.objects.none()


class AdminDashboardView(APIView):
    """View for admin dashboard overview (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard overview data"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dashboard_service = AdminDashboardService()
        overview = dashboard_service.get_dashboard_overview()
        
        serializer = DashboardOverviewSerializer(overview)
        return Response(serializer.data)


class RecentActivityView(APIView):
    """View for recent platform activity (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get recent activity"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        limit = int(request.query_params.get('limit', 20))
        dashboard_service = AdminDashboardService()
        activities = dashboard_service.get_recent_activity(limit=limit)
        
        serializer = RecentActivitySerializer(activities, many=True)
        return Response(serializer.data)


class SystemHealthView(APIView):
    """View for system health status (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get system health status"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dashboard_service = AdminDashboardService()
        health = dashboard_service.get_system_health()
        
        serializer = SystemHealthSerializer(health)
        return Response(serializer.data)


class UserManagementView(APIView):
    """View for user management operations (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id, action):
        """Perform user management action"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = get_object_or_404(User, id=user_id)
        user_service = UserManagementService()
        
        if action == 'suspend':
            serializer = UserSuspendSerializer(data=request.data)
            if serializer.is_valid():
                success = user_service.suspend_user(
                    user=user,
                    admin=request.user,
                    reason=serializer.validated_data['reason'],
                    duration_days=serializer.validated_data.get('duration_days')
                )
                if success:
                    return Response({'message': 'User suspended successfully'})
                else:
                    return Response(
                        {'error': 'Failed to suspend user'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'ban':
            serializer = UserBanSerializer(data=request.data)
            if serializer.is_valid():
                success = user_service.ban_user(
                    user=user,
                    admin=request.user,
                    reason=serializer.validated_data['reason']
                )
                if success:
                    return Response({'message': 'User banned successfully'})
                else:
                    return Response(
                        {'error': 'Failed to ban user'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'verify':
            serializer = UserVerifySerializer(data=request.data)
            if serializer.is_valid():
                success = user_service.verify_user(
                    user=user,
                    admin=request.user,
                    reason=serializer.validated_data.get('reason', '')
                )
                if success:
                    return Response({'message': 'User verified successfully'})
                else:
                    return Response(
                        {'error': 'Failed to verify user'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'adjust-wallet':
            serializer = WalletAdjustSerializer(data=request.data)
            if serializer.is_valid():
                success = user_service.adjust_wallet(
                    user=user,
                    admin=request.user,
                    amount=serializer.validated_data['amount'],
                    reason=serializer.validated_data['reason']
                )
                if success:
                    return Response({'message': 'Wallet adjusted successfully'})
                else:
                    return Response(
                        {'error': 'Failed to adjust wallet'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CampaignManagementView(APIView):
    """View for campaign management operations (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, campaign_id, action):
        """Perform campaign management action"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        campaign = get_object_or_404(Campaign, id=campaign_id)
        campaign_service = CampaignManagementService()
        
        if action == 'pause':
            serializer = CampaignPauseSerializer(data=request.data)
            if serializer.is_valid():
                success = campaign_service.pause_campaign(
                    campaign=campaign,
                    admin=request.user,
                    reason=serializer.validated_data['reason']
                )
                if success:
                    return Response({'message': 'Campaign paused successfully'})
                else:
                    return Response(
                        {'error': 'Failed to pause campaign'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'cancel':
            serializer = CampaignCancelSerializer(data=request.data)
            if serializer.is_valid():
                success = campaign_service.cancel_campaign(
                    campaign=campaign,
                    admin=request.user,
                    reason=serializer.validated_data['reason']
                )
                if success:
                    return Response({'message': 'Campaign cancelled successfully'})
                else:
                    return Response(
                        {'error': 'Failed to cancel campaign'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )


class FinancialManagementView(APIView):
    """View for financial management operations (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, withdrawal_id, action):
        """Perform financial management action"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
        financial_service = FinancialManagementService()
        
        if action == 'approve':
            serializer = WithdrawalApproveSerializer(data=request.data)
            if serializer.is_valid():
                success = financial_service.approve_withdrawal(
                    withdrawal=withdrawal,
                    admin=request.user,
                    notes=serializer.validated_data.get('notes', '')
                )
                if success:
                    return Response({'message': 'Withdrawal approved successfully'})
                else:
                    return Response(
                        {'error': 'Failed to approve withdrawal'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'reject':
            serializer = WithdrawalRejectSerializer(data=request.data)
            if serializer.is_valid():
                success = financial_service.reject_withdrawal(
                    withdrawal=withdrawal,
                    admin=request.user,
                    reason=serializer.validated_data['reason']
                )
                if success:
                    return Response({'message': 'Withdrawal rejected successfully'})
                else:
                    return Response(
                        {'error': 'Failed to reject withdrawal'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ConfigurationManagementView(APIView):
    """View for configuration management (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current configuration"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        config_service = SystemConfigurationService()
        configuration = config_service.get_configuration()
        
        return Response(configuration)
    
    def post(self, request):
        """Update configuration"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ConfigurationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            config_service = SystemConfigurationService()
            success = config_service.update_configuration(
                key=serializer.validated_data['key'],
                value=serializer.validated_data['value'],
                admin=request.user,
                reason=serializer.validated_data.get('reason', '')
            )
            
            if success:
                return Response({'message': 'Configuration updated successfully'})
            else:
                return Response(
                    {'error': 'Failed to update configuration'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkActionView(APIView):
    """View for bulk actions (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Perform bulk action"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BulkActionSerializer(data=request.data)
        if serializer.is_valid():
            action_type = serializer.validated_data['action_type']
            target_ids = serializer.validated_data['target_ids']
            reason = serializer.validated_data['reason']
            
            # This would implement bulk operations
            # For now, return a placeholder response
            return Response({
                'message': f'Bulk action {action_type} initiated',
                'target_count': len(target_ids),
                'status': 'processing'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(APIView):
    """View for user search (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Search users"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserSearchSerializer(data=request.query_params)
        if serializer.is_valid():
            # This would implement user search
            # For now, return a placeholder response
            return Response({
                'users': [],
                'total_count': 0,
                'page': 1,
                'page_size': 20
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CampaignSearchView(APIView):
    """View for campaign search (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Search campaigns"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CampaignSearchSerializer(data=request.query_params)
        if serializer.is_valid():
            # This would implement campaign search
            # For now, return a placeholder response
            return Response({
                'campaigns': [],
                'total_count': 0,
                'page': 1,
                'page_size': 20
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WithdrawalSearchView(APIView):
    """View for withdrawal search (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Search withdrawals"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = WithdrawalSearchSerializer(data=request.query_params)
        if serializer.is_valid():
            # This would implement withdrawal search
            # For now, return a placeholder response
            return Response({
                'withdrawals': [],
                'total_count': 0,
                'page': 1,
                'page_size': 20
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)