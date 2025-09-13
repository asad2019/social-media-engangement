from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    VerificationRule, VerificationSession, VerificationLog,
    ManualReviewQueue, FraudDetection, FraudAlert
)
from .serializers import (
    VerificationRuleSerializer, VerificationRuleCreateSerializer,
    VerificationSessionSerializer, VerificationLogSerializer,
    ManualReviewQueueSerializer, ManualReviewActionSerializer,
    FraudDetectionSerializer, FraudAlertSerializer, FraudAlertResolutionSerializer,
    VerificationStatsSerializer, UserFraudAnalysisSerializer, VerificationTestSerializer
)
from .services import VerificationService, ManualReviewService, FraudDetectionService


class VerificationRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for verification rules (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = VerificationRule.objects.all()
    
    def get_queryset(self):
        # Only admins and moderators can access verification rules
        if self.request.user.role in ['admin', 'moderator']:
            return VerificationRule.objects.all()
        return VerificationRule.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VerificationRuleCreateSerializer
        return VerificationRuleSerializer
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a verification rule"""
        rule = self.get_object()
        
        serializer = VerificationTestSerializer(data=request.data)
        if serializer.is_valid():
            # This would run a test verification
            # For now, return a placeholder response
            return Response({
                'rule_id': str(rule.id),
                'test_result': 'success',
                'confidence': 0.8,
                'methods_tested': rule.verification_methods,
                'message': 'Test verification completed successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerificationSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for verification sessions (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = VerificationSession.objects.all()
    serializer_class = VerificationSessionSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access verification sessions
        if self.request.user.role in ['admin', 'moderator']:
            return VerificationSession.objects.all()
        return VerificationSession.objects.none()


class ManualReviewQueueViewSet(viewsets.ModelViewSet):
    """ViewSet for manual review queue (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = ManualReviewQueue.objects.all()
    serializer_class = ManualReviewQueueSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access manual review queue
        if self.request.user.role in ['admin', 'moderator']:
            return ManualReviewQueue.objects.all()
        return ManualReviewQueue.objects.none()
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review a manual review item"""
        review = self.get_object()
        
        serializer = ManualReviewActionSerializer(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data['action']
            notes = serializer.validated_data.get('notes', '')
            
            review_service = ManualReviewService()
            
            if action == 'approve':
                success = review_service.approve_review(
                    review_id=str(review.id),
                    reviewer=request.user,
                    notes=notes
                )
            else:  # reject
                success = review_service.reject_review(
                    review_id=str(review.id),
                    reviewer=request.user,
                    reason=notes
                )
            
            if success:
                return Response({'message': f'Review {action}d successfully'})
            else:
                return Response(
                    {'error': 'Failed to process review'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending manual reviews"""
        limit = request.query_params.get('limit', 50)
        try:
            limit = int(limit)
        except ValueError:
            limit = 50
        
        review_service = ManualReviewService()
        pending_reviews = review_service.get_pending_reviews(limit=limit)
        
        serializer = ManualReviewQueueSerializer(pending_reviews, many=True)
        return Response(serializer.data)


class FraudDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for fraud detection records (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = FraudDetection.objects.all()
    serializer_class = FraudDetectionSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access fraud detection records
        if self.request.user.role in ['admin', 'moderator']:
            return FraudDetection.objects.all()
        return FraudDetection.objects.none()


class FraudAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for fraud alerts (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = FraudAlert.objects.all()
    serializer_class = FraudAlertSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access fraud alerts
        if self.request.user.role in ['admin', 'moderator']:
            return FraudAlert.objects.all()
        return FraudAlert.objects.none()
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a fraud alert"""
        alert = self.get_object()
        
        serializer = FraudAlertResolutionSerializer(data=request.data)
        if serializer.is_valid():
            resolution_notes = serializer.validated_data.get('resolution_notes', '')
            
            alert.status = 'resolved'
            alert.resolved_at = timezone.now()
            alert.resolved_by = request.user
            alert.resolution_notes = resolution_notes
            alert.save()
            
            return Response({'message': 'Fraud alert resolved successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active fraud alerts"""
        active_alerts = FraudAlert.objects.filter(status='active')
        serializer = FraudAlertSerializer(active_alerts, many=True)
        return Response(serializer.data)


class VerificationStatsView(APIView):
    """View for verification statistics (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get verification statistics"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get verification sessions
        sessions = VerificationSession.objects.filter(created_at__gte=start_date)
        
        total_verifications = sessions.count()
        verified_count = sessions.filter(status='verified').count()
        rejected_count = sessions.filter(status='rejected').count()
        manual_review_count = sessions.filter(status='manual_review').count()
        
        # Get fraud detection count
        fraud_detected_count = FraudDetection.objects.filter(
            detected_at__gte=start_date
        ).count()
        
        # Calculate average confidence
        avg_confidence = sessions.aggregate(
            avg_confidence=Avg('confidence')
        )['avg_confidence'] or 0.0
        
        # Calculate success rate
        success_rate = (verified_count / total_verifications * 100) if total_verifications > 0 else 0.0
        
        stats = {
            'total_verifications': total_verifications,
            'verified_count': verified_count,
            'rejected_count': rejected_count,
            'manual_review_count': manual_review_count,
            'fraud_detected_count': fraud_detected_count,
            'average_confidence': round(avg_confidence, 3),
            'success_rate': round(success_rate, 2)
        }
        
        serializer = VerificationStatsSerializer(stats)
        return Response(serializer.data)


class UserFraudAnalysisView(APIView):
    """View for analyzing user fraud patterns (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        """Get fraud analysis for a specific user"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from users.models import User
        user = get_object_or_404(User, id=user_id)
        
        fraud_service = FraudDetectionService()
        analysis = fraud_service.analyze_user_patterns(user)
        
        serializer = UserFraudAnalysisSerializer(analysis)
        return Response(serializer.data)
    
    def post(self, request, user_id):
        """Create a fraud alert for a user"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from users.models import User
        user = get_object_or_404(User, id=user_id)
        
        reason = request.data.get('reason', '')
        severity = request.data.get('severity', 'medium')
        
        if not reason:
            return Response(
                {'error': 'Reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fraud_service = FraudDetectionService()
        alert = fraud_service.create_fraud_alert(user, reason, severity)
        
        serializer = FraudAlertSerializer(alert)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VerificationTestView(APIView):
    """View for testing verification methods (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Test verification methods"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = VerificationTestSerializer(data=request.data)
        if serializer.is_valid():
            # This would run actual verification tests
            # For now, return a placeholder response
            return Response({
                'test_id': 'test_123',
                'status': 'completed',
                'results': {
                    'deterministic': {'confidence': 0.8, 'status': 'passed'},
                    'tokenized': {'confidence': 0.7, 'status': 'passed'},
                    'screenshot': {'confidence': 0.6, 'status': 'manual_review'},
                },
                'overall_confidence': 0.7,
                'recommendation': 'manual_review'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerificationHealthView(APIView):
    """View for verification system health check"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get verification system health status"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check ML service health
        ml_service_healthy = True
        try:
            import httpx
            import asyncio
            
            async def check_ml_service():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{settings.ML_SERVICE_URL}/health",
                            timeout=5.0
                        )
                        return response.status_code == 200
                except:
                    return False
            
            ml_service_healthy = asyncio.run(check_ml_service())
        except:
            ml_service_healthy = False
        
        # Check pending manual reviews
        pending_reviews = ManualReviewQueue.objects.filter(status='pending').count()
        
        # Check active fraud alerts
        active_alerts = FraudAlert.objects.filter(status='active').count()
        
        health_status = {
            'ml_service_healthy': ml_service_healthy,
            'pending_manual_reviews': pending_reviews,
            'active_fraud_alerts': active_alerts,
            'system_status': 'healthy' if ml_service_healthy and pending_reviews < 100 else 'degraded'
        }
        
        return Response(health_status)