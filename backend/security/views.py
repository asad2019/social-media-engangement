from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import SecurityEvent, AuditLog, DataAccessLog
from .serializers import (
    SecurityEventSerializer, AuditLogSerializer, DataAccessLogSerializer,
    SecurityAnalysisSerializer, AnomalySerializer, IPThreatSerializer,
    GDPRReportSerializer, ComplianceActionSerializer
)
from .services import (
    SecurityMonitoringService, ComplianceService, ThreatDetectionService
)


class SecurityEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for security events (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access security events
        if self.request.user.role in ['admin', 'moderator']:
            return SecurityEvent.objects.all()
        return SecurityEvent.objects.none()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audit logs (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access audit logs
        if self.request.user.role in ['admin', 'moderator']:
            return AuditLog.objects.all()
        return AuditLog.objects.none()


class DataAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for data access logs (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = DataAccessLog.objects.all()
    serializer_class = DataAccessLogSerializer
    
    def get_queryset(self):
        # Only admins and moderators can access data access logs
        if self.request.user.role in ['admin', 'moderator']:
            return DataAccessLog.objects.all()
        return DataAccessLog.objects.none()


class SecurityAnalysisView(APIView):
    """View for security analysis (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get security analysis"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        hours = int(request.query_params.get('hours', 24))
        monitoring_service = SecurityMonitoringService()
        analysis = monitoring_service.analyze_security_events(hours=hours)
        
        serializer = SecurityAnalysisSerializer(analysis)
        return Response(serializer.data)


class AnomalyDetectionView(APIView):
    """View for anomaly detection (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get detected anomalies"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        monitoring_service = SecurityMonitoringService()
        anomalies = monitoring_service.detect_anomalies()
        
        serializer = AnomalySerializer(anomalies, many=True)
        return Response(serializer.data)


class IPThreatAnalysisView(APIView):
    """View for IP threat analysis (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, ip_address):
        """Analyze IP threat"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        threat_service = ThreatDetectionService()
        analysis = threat_service.analyze_ip_threat(ip_address)
        
        serializer = IPThreatSerializer(analysis)
        return Response(serializer.data)


class BlockIPView(APIView):
    """View for blocking IP addresses (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Block an IP address"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ip_address = request.data.get('ip_address')
        reason = request.data.get('reason', 'Manual block')
        
        if not ip_address:
            return Response(
                {'error': 'IP address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        threat_service = ThreatDetectionService()
        success = threat_service.block_suspicious_ip(ip_address, reason)
        
        if success:
            return Response({'message': f'IP {ip_address} blocked successfully'})
        else:
            return Response(
                {'error': 'Failed to block IP address'},
                status=status.HTTP_400_BAD_REQUEST
            )


class GDPRReportView(APIView):
    """View for GDPR compliance reports (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        """Generate GDPR report for user"""
        if request.user.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        compliance_service = ComplianceService()
        report = compliance_service.generate_gdpr_report(user_id)
        
        if 'error' in report:
            return Response(
                {'error': report['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = GDPRReportSerializer(report)
        return Response(serializer.data)


class AnonymizeUserView(APIView):
    """View for anonymizing user data (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        """Anonymize user data"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        compliance_service = ComplianceService()
        success = compliance_service.anonymize_user_data(user_id)
        
        if success:
            return Response({'message': 'User data anonymized successfully'})
        else:
            return Response(
                {'error': 'Failed to anonymize user data'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DeleteUserView(APIView):
    """View for deleting user data (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        """Delete user data"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        compliance_service = ComplianceService()
        success = compliance_service.delete_user_data(user_id)
        
        if success:
            return Response({'message': 'User data deleted successfully'})
        else:
            return Response(
                {'error': 'Failed to delete user data'},
                status=status.HTTP_400_BAD_REQUEST
            )