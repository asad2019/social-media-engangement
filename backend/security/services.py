import logging
import hashlib
import json
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta, datetime
from decimal import Decimal

from .models import SecurityEvent, AuditLog, DataAccessLog
from users.models import User

logger = logging.getLogger(__name__)


class SecurityMonitoringService:
    """Service for security monitoring and threat detection"""
    
    def analyze_security_events(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze security events for the last N hours"""
        try:
            since = timezone.now() - timedelta(hours=hours)
            
            # Get events
            events = SecurityEvent.objects.filter(timestamp__gte=since)
            
            # Analyze by type
            event_types = events.values('event_type').annotate(count=Count('id'))
            
            # Analyze by severity
            severity_counts = events.values('severity').annotate(count=Count('id'))
            
            # Analyze by IP
            ip_counts = events.values('ip_address').annotate(count=Count('id')).order_by('-count')[:10]
            
            # Analyze failed logins
            failed_logins = events.filter(event_type='login_failed').count()
            
            # Analyze suspicious activity
            suspicious_activity = events.filter(event_type='suspicious_activity').count()
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(events)
            
            return {
                'total_events': events.count(),
                'event_types': list(event_types),
                'severity_counts': list(severity_counts),
                'top_ips': list(ip_counts),
                'failed_logins': failed_logins,
                'suspicious_activity': suspicious_activity,
                'risk_score': risk_score,
                'time_period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze security events: {e}")
            return {}
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect security anomalies"""
        anomalies = []
        
        try:
            # Check for unusual login patterns
            login_anomalies = self._detect_login_anomalies()
            anomalies.extend(login_anomalies)
            
            # Check for unusual API usage
            api_anomalies = self._detect_api_anomalies()
            anomalies.extend(api_anomalies)
            
            # Check for unusual data access patterns
            data_anomalies = self._detect_data_access_anomalies()
            anomalies.extend(data_anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return []
    
    def _calculate_risk_score(self, events) -> float:
        """Calculate overall risk score"""
        if not events.exists():
            return 0.0
        
        # Weight different event types
        weights = {
            'login_failed': 0.3,
            'suspicious_activity': 0.5,
            'fraud_detection': 0.8,
            'admin_action': 0.2,
            'data_modification': 0.4,
        }
        
        # Weight different severities
        severity_weights = {
            'low': 0.1,
            'medium': 0.3,
            'high': 0.6,
            'critical': 1.0,
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for event in events:
            event_weight = weights.get(event.event_type, 0.1)
            severity_weight = severity_weights.get(event.severity, 0.3)
            
            score = event_weight * severity_weight
            total_score += score
            total_weight += event_weight
        
        if total_weight == 0:
            return 0.0
        
        return min(1.0, total_score / total_weight)
    
    def _detect_login_anomalies(self) -> List[Dict[str, Any]]:
        """Detect login anomalies"""
        anomalies = []
        
        # Check for multiple failed logins from same IP
        since = timezone.now() - timedelta(hours=1)
        failed_logins = SecurityEvent.objects.filter(
            event_type='login_failed',
            timestamp__gte=since
        )
        
        ip_counts = failed_logins.values('ip_address').annotate(count=Count('id'))
        
        for ip_data in ip_counts:
            if ip_data['count'] > 10:  # More than 10 failed logins in 1 hour
                anomalies.append({
                    'type': 'multiple_failed_logins',
                    'severity': 'high',
                    'description': f"Multiple failed logins from IP {ip_data['ip_address']}",
                    'count': ip_data['count'],
                    'ip_address': ip_data['ip_address']
                })
        
        return anomalies
    
    def _detect_api_anomalies(self) -> List[Dict[str, Any]]:
        """Detect API usage anomalies"""
        anomalies = []
        
        # Check for unusual API usage patterns
        since = timezone.now() - timedelta(hours=1)
        api_events = SecurityEvent.objects.filter(
            event_type='api_access',
            timestamp__gte=since
        )
        
        # Check for rapid API calls
        user_counts = api_events.values('user').annotate(count=Count('id'))
        
        for user_data in user_counts:
            if user_data['count'] > 1000:  # More than 1000 API calls in 1 hour
                anomalies.append({
                    'type': 'rapid_api_calls',
                    'severity': 'medium',
                    'description': f"User {user_data['user']} made {user_data['count']} API calls in 1 hour",
                    'count': user_data['count'],
                    'user_id': user_data['user']
                })
        
        return anomalies
    
    def _detect_data_access_anomalies(self) -> List[Dict[str, Any]]:
        """Detect data access anomalies"""
        anomalies = []
        
        # Check for unusual data access patterns
        since = timezone.now() - timedelta(hours=24)
        data_access = DataAccessLog.objects.filter(timestamp__gte=since)
        
        # Check for bulk data access
        user_counts = data_access.values('user').annotate(count=Count('id'))
        
        for user_data in user_counts:
            if user_data['count'] > 1000:  # More than 1000 data access events in 24 hours
                anomalies.append({
                    'type': 'bulk_data_access',
                    'severity': 'high',
                    'description': f"User {user_data['user']} accessed data {user_data['count']} times in 24 hours",
                    'count': user_data['count'],
                    'user_id': user_data['user']
                })
        
        return anomalies


class ComplianceService:
    """Service for compliance and privacy management"""
    
    def generate_gdpr_report(self, user_id: str) -> Dict[str, Any]:
        """Generate GDPR compliance report for a user"""
        try:
            user = User.objects.get(id=user_id)
            
            # Collect user data
            user_data = {
                'profile': {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                },
                'kyc_status': user.kyc_status,
                'wallet_balance': float(user.wallet_balance),
                'reputation_score': user.reputation_score,
            }
            
            # Collect audit logs
            audit_logs = AuditLog.objects.filter(user=user).order_by('-timestamp')
            user_data['audit_logs'] = [
                {
                    'action': log.action,
                    'model_name': log.model_name,
                    'timestamp': log.timestamp.isoformat(),
                    'ip_address': log.ip_address,
                }
                for log in audit_logs[:100]  # Limit to last 100
            ]
            
            # Collect security events
            security_events = SecurityEvent.objects.filter(user=user).order_by('-timestamp')
            user_data['security_events'] = [
                {
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'timestamp': event.timestamp.isoformat(),
                    'ip_address': event.ip_address,
                }
                for event in security_events[:50]  # Limit to last 50
            ]
            
            # Collect data access logs
            data_access = DataAccessLog.objects.filter(user=user).order_by('-timestamp')
            user_data['data_access'] = [
                {
                    'access_type': access.access_type,
                    'model_name': access.model_name,
                    'timestamp': access.timestamp.isoformat(),
                    'ip_address': access.ip_address,
                }
                for access in data_access[:50]  # Limit to last 50
            ]
            
            return {
                'user_id': str(user.id),
                'generated_at': timezone.now().isoformat(),
                'data': user_data,
                'summary': {
                    'total_audit_logs': audit_logs.count(),
                    'total_security_events': security_events.count(),
                    'total_data_access': data_access.count(),
                }
            }
            
        except User.DoesNotExist:
            return {'error': 'User not found'}
        except Exception as e:
            logger.error(f"Failed to generate GDPR report: {e}")
            return {'error': str(e)}
    
    def anonymize_user_data(self, user_id: str) -> bool:
        """Anonymize user data for GDPR compliance"""
        try:
            user = User.objects.get(id=user_id)
            
            # Anonymize user profile
            user.username = f"anonymized_{user.id}"
            user.email = f"anonymized_{user.id}@example.com"
            user.first_name = "Anonymized"
            user.last_name = "User"
            user.save()
            
            # Log the anonymization
            SecurityEvent.objects.create(
                user=user,
                event_type='data_modification',
                severity='high',
                description=f"User data anonymized for GDPR compliance",
                metadata={
                    'anonymization_date': timezone.now().isoformat(),
                    'reason': 'gdpr_compliance'
                }
            )
            
            logger.info(f"User {user_id} data anonymized for GDPR compliance")
            return True
            
        except User.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to anonymize user data: {e}")
            return False
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete user data for GDPR compliance"""
        try:
            user = User.objects.get(id=user_id)
            
            # Log the deletion
            SecurityEvent.objects.create(
                user=user,
                event_type='data_modification',
                severity='critical',
                description=f"User data deleted for GDPR compliance",
                metadata={
                    'deletion_date': timezone.now().isoformat(),
                    'reason': 'gdpr_compliance'
                }
            )
            
            # Soft delete the user
            user.is_active = False
            user.save()
            
            logger.info(f"User {user_id} data deleted for GDPR compliance")
            return True
            
        except User.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False


class ThreatDetectionService:
    """Service for threat detection and prevention"""
    
    def analyze_ip_threat(self, ip_address: str) -> Dict[str, Any]:
        """Analyze IP address for threats"""
        try:
            # Get recent events from this IP
            since = timezone.now() - timedelta(hours=24)
            events = SecurityEvent.objects.filter(
                ip_address=ip_address,
                timestamp__gte=since
            )
            
            # Calculate threat score
            threat_score = 0.0
            
            # Failed logins
            failed_logins = events.filter(event_type='login_failed').count()
            if failed_logins > 0:
                threat_score += min(0.5, failed_logins * 0.1)
            
            # Suspicious activity
            suspicious_activity = events.filter(event_type='suspicious_activity').count()
            if suspicious_activity > 0:
                threat_score += min(0.3, suspicious_activity * 0.2)
            
            # Fraud detection
            fraud_events = events.filter(event_type='fraud_detection').count()
            if fraud_events > 0:
                threat_score += min(0.4, fraud_events * 0.3)
            
            # Determine threat level
            if threat_score >= 0.8:
                threat_level = 'critical'
            elif threat_score >= 0.6:
                threat_level = 'high'
            elif threat_score >= 0.4:
                threat_level = 'medium'
            elif threat_score >= 0.2:
                threat_level = 'low'
            else:
                threat_level = 'minimal'
            
            return {
                'ip_address': ip_address,
                'threat_score': threat_score,
                'threat_level': threat_level,
                'total_events': events.count(),
                'failed_logins': failed_logins,
                'suspicious_activity': suspicious_activity,
                'fraud_events': fraud_events,
                'analysis_period_hours': 24
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze IP threat: {e}")
            return {'error': str(e)}
    
    def block_suspicious_ip(self, ip_address: str, reason: str) -> bool:
        """Block a suspicious IP address"""
        try:
            # Add to cache for blocking
            cache_key = f"blocked_ip:{ip_address}"
            cache.set(cache_key, {
                'blocked_at': timezone.now().isoformat(),
                'reason': reason,
                'blocked_by': 'system'
            }, timeout=86400)  # Block for 24 hours
            
            # Log the blocking
            SecurityEvent.objects.create(
                user=None,
                event_type='suspicious_activity',
                severity='high',
                description=f"IP {ip_address} blocked: {reason}",
                ip_address=ip_address,
                metadata={
                    'blocked_at': timezone.now().isoformat(),
                    'reason': reason,
                    'action': 'ip_blocked'
                }
            )
            
            logger.info(f"IP {ip_address} blocked: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to block IP {ip_address}: {e}")
            return False
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        cache_key = f"blocked_ip:{ip_address}"
        return cache.get(cache_key) is not None
