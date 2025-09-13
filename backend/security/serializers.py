from rest_framework import serializers
from .models import SecurityEvent, AuditLog, DataAccessLog


class SecurityEventSerializer(serializers.ModelSerializer):
    """Serializer for security events"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'user_username', 'event_type', 'severity', 'description',
            'ip_address', 'user_agent', 'session_id', 'request_path',
            'request_method', 'metadata', 'risk_score', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user_username', 'action', 'model_name', 'object_id',
            'object_repr', 'old_values', 'new_values', 'changed_fields',
            'ip_address', 'user_agent', 'request_path', 'request_method',
            'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class DataAccessLogSerializer(serializers.ModelSerializer):
    """Serializer for data access logs"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DataAccessLog
        fields = [
            'id', 'user_username', 'access_type', 'model_name', 'object_id',
            'object_repr', 'ip_address', 'user_agent', 'request_path',
            'request_method', 'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class SecurityAnalysisSerializer(serializers.Serializer):
    """Serializer for security analysis data"""
    total_events = serializers.IntegerField()
    event_types = serializers.ListField()
    severity_counts = serializers.ListField()
    top_ips = serializers.ListField()
    failed_logins = serializers.IntegerField()
    suspicious_activity = serializers.IntegerField()
    risk_score = serializers.FloatField()
    time_period_hours = serializers.IntegerField()


class AnomalySerializer(serializers.Serializer):
    """Serializer for security anomalies"""
    type = serializers.CharField()
    severity = serializers.CharField()
    description = serializers.CharField()
    count = serializers.IntegerField(required=False)
    ip_address = serializers.IPAddressField(required=False)
    user_id = serializers.UUIDField(required=False)


class IPThreatSerializer(serializers.Serializer):
    """Serializer for IP threat analysis"""
    ip_address = serializers.IPAddressField()
    threat_score = serializers.FloatField()
    threat_level = serializers.CharField()
    total_events = serializers.IntegerField()
    failed_logins = serializers.IntegerField()
    suspicious_activity = serializers.IntegerField()
    fraud_events = serializers.IntegerField()
    analysis_period_hours = serializers.IntegerField()


class GDPRReportSerializer(serializers.Serializer):
    """Serializer for GDPR compliance reports"""
    user_id = serializers.UUIDField()
    generated_at = serializers.DateTimeField()
    data = serializers.DictField()
    summary = serializers.DictField()


class ComplianceActionSerializer(serializers.Serializer):
    """Serializer for compliance actions"""
    action = serializers.ChoiceField(choices=['anonymize', 'delete'])
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_reason(self, value):
        """Validate reason length"""
        if len(value) > 500:
            raise serializers.ValidationError("Reason cannot exceed 500 characters")
        return value
