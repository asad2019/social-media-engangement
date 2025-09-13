import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponseForbidden, HttpResponseTooManyRequests
from django.conf import settings
from django.utils import timezone
from .models import SecurityEvent, AuditLog, DataAccessLog

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """Middleware for security monitoring and rate limiting"""
    
    def process_request(self, request):
        """Process incoming request for security checks"""
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Rate limiting
        if self.is_rate_limited(request, ip_address):
            return HttpResponseTooManyRequests("Rate limit exceeded")
        
        # Log API access
        if request.path.startswith('/api/'):
            self.log_api_access(request, ip_address)
        
        # Check for suspicious patterns
        if self.is_suspicious_request(request, ip_address):
            self.log_suspicious_activity(request, ip_address)
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response for security logging"""
        # Log data access for sensitive endpoints
        if self.is_sensitive_endpoint(request):
            self.log_data_access(request, response)
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, request, ip_address):
        """Check if request exceeds rate limit"""
        # Different rate limits for different endpoints
        if request.path.startswith('/api/v1/auth/'):
            limit = 10  # 10 requests per minute for auth
            window = 60
        elif request.path.startswith('/api/'):
            limit = 100  # 100 requests per minute for API
            window = 60
        else:
            limit = 200  # 200 requests per minute for general
            window = 60
        
        # Create cache key
        cache_key = f"rate_limit:{ip_address}:{request.path}"
        
        # Check current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return True
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window)
        
        return False
    
    def log_api_access(self, request, ip_address):
        """Log API access"""
        try:
            SecurityEvent.objects.create(
                user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
                event_type='api_access',
                severity='low',
                description=f"API access: {request.method} {request.path}",
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_path=request.path,
                request_method=request.method,
                metadata={
                    'query_params': dict(request.GET),
                    'content_type': request.META.get('CONTENT_TYPE', ''),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log API access: {e}")
    
    def is_suspicious_request(self, request, ip_address):
        """Check for suspicious request patterns"""
        suspicious_indicators = []
        
        # Check for SQL injection patterns
        query_string = request.META.get('QUERY_STRING', '')
        if any(pattern in query_string.lower() for pattern in ['union', 'select', 'drop', 'delete', 'insert']):
            suspicious_indicators.append('sql_injection_pattern')
        
        # Check for XSS patterns
        if any(pattern in query_string.lower() for pattern in ['<script', 'javascript:', 'onload=']):
            suspicious_indicators.append('xss_pattern')
        
        # Check for unusual user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if len(user_agent) > 500 or not user_agent:
            suspicious_indicators.append('unusual_user_agent')
        
        # Check for rapid requests from same IP
        cache_key = f"rapid_requests:{ip_address}"
        rapid_count = cache.get(cache_key, 0)
        if rapid_count > 50:  # More than 50 requests in last minute
            suspicious_indicators.append('rapid_requests')
        
        cache.set(cache_key, rapid_count + 1, 60)
        
        return len(suspicious_indicators) > 0
    
    def log_suspicious_activity(self, request, ip_address):
        """Log suspicious activity"""
        try:
            SecurityEvent.objects.create(
                user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
                event_type='suspicious_activity',
                severity='high',
                description=f"Suspicious activity detected from {ip_address}",
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_path=request.path,
                request_method=request.method,
                metadata={
                    'query_string': request.META.get('QUERY_STRING', ''),
                    'headers': dict(request.META),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log suspicious activity: {e}")
    
    def is_sensitive_endpoint(self, request):
        """Check if endpoint is sensitive and requires data access logging"""
        sensitive_paths = [
            '/api/v1/users/',
            '/api/v1/campaigns/',
            '/api/v1/jobs/',
            '/api/v1/wallets/',
            '/api/v1/admin/',
        ]
        
        return any(request.path.startswith(path) for path in sensitive_paths)
    
    def log_data_access(self, request, response):
        """Log data access for compliance"""
        try:
            # Only log successful requests
            if response.status_code < 400:
                DataAccessLog.objects.create(
                    user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
                    access_type='api_access',
                    model_name=self.get_model_from_path(request.path),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    request_method=request.method,
                    metadata={
                        'response_status': response.status_code,
                        'content_type': response.get('Content-Type', ''),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
    
    def get_model_from_path(self, path):
        """Extract model name from API path"""
        if '/users/' in path:
            return 'User'
        elif '/campaigns/' in path:
            return 'Campaign'
        elif '/jobs/' in path:
            return 'Job'
        elif '/wallets/' in path:
            return 'WalletTransaction'
        elif '/admin/' in path:
            return 'AdminAction'
        else:
            return 'Unknown'


class AuditMiddleware(MiddlewareMixin):
    """Middleware for automatic audit logging"""
    
    def process_request(self, request):
        """Store request info for audit logging"""
        request._audit_start_time = time.time()
        request._audit_ip = self.get_client_ip(request)
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')
        return None
    
    def process_response(self, request, response):
        """Log audit information"""
        if hasattr(request, '_audit_start_time'):
            # Only log for authenticated users and API endpoints
            if (hasattr(request, 'user') and request.user.is_authenticated and 
                request.path.startswith('/api/')):
                
                self.log_audit_event(request, response)
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_audit_event(self, request, response):
        """Log audit event"""
        try:
            # Determine action type
            action = self.get_action_type(request.method, response.status_code)
            
            # Get model and object info
            model_name, object_id, object_repr = self.get_object_info(request, response)
            
            AuditLog.objects.create(
                user=request.user,
                action=action,
                model_name=model_name,
                object_id=object_id,
                object_repr=object_repr,
                ip_address=getattr(request, '_audit_ip', ''),
                user_agent=getattr(request, '_audit_user_agent', ''),
                request_path=request.path,
                request_method=request.method,
                metadata={
                    'response_status': response.status_code,
                    'processing_time': time.time() - getattr(request, '_audit_start_time', 0),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def get_action_type(self, method, status_code):
        """Determine action type from HTTP method and status"""
        if method == 'POST' and status_code < 400:
            return 'create'
        elif method == 'PUT' and status_code < 400:
            return 'update'
        elif method == 'PATCH' and status_code < 400:
            return 'update'
        elif method == 'DELETE' and status_code < 400:
            return 'delete'
        elif method == 'GET':
            return 'read'
        else:
            return 'unknown'
    
    def get_object_info(self, request, response):
        """Extract object information from request/response"""
        # Extract from URL path
        path_parts = request.path.strip('/').split('/')
        
        if len(path_parts) >= 3:  # /api/v1/model/id/
            model_name = path_parts[2].title()
            if len(path_parts) >= 4:
                object_id = path_parts[3]
            else:
                object_id = 'list'
        else:
            model_name = 'Unknown'
            object_id = 'unknown'
        
        # Try to get object representation from response
        object_repr = f"{model_name}:{object_id}"
        
        return model_name, object_id, object_repr
