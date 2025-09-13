from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import login, logout
from django.utils import timezone
from django.conf import settings
from .models import User, SocialAccount, AuditLog
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UpdateProfileSerializer, KYCSerializer, SocialAccountSerializer,
    SocialAccountCreateSerializer, AuditLogSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)


class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create audit log
            AuditLog.objects.create(
                actor=user,
                action='user_create',
                target_type='User',
                target_id=user.id,
                description=f'User {user.username} registered',
                metadata={'role': user.role},
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginView(TokenObtainPairView):
    """User login endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create audit log
            AuditLog.objects.create(
                actor=user,
                action='user_login',
                target_type='User',
                target_id=user.id,
                description=f'User {user.username} logged in',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Create audit log
            AuditLog.objects.create(
                actor=request.user,
                action='user_logout',
                target_type='User',
                target_id=request.user.id,
                description=f'User {request.user.username} logged out',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(APIView):
    """Get user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UpdateProfileView(APIView):
    """Update user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Create audit log
            AuditLog.objects.create(
                actor=request.user,
                action='user_update',
                target_type='User',
                target_id=request.user.id,
                description=f'User {request.user.username} updated profile',
                metadata={'updated_fields': list(request.data.keys())},
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response(UserProfileSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SubmitKYCView(APIView):
    """Submit KYC documents"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = KYCSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            user.kyc_status = 'pending'
            user.save()
            return Response({'message': 'KYC documents submitted successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KYCStatusView(APIView):
    """Get KYC status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'kyc_status': request.user.kyc_status,
            'can_withdraw': request.user.can_withdraw(),
            'kyc_required_threshold': getattr(settings, 'KYC_REQUIRED_THRESHOLD', 100.00)
        })


class SocialAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for social accounts"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = SocialAccount.objects.all()
    
    def get_queryset(self):
        return SocialAccount.objects.filter(user=self.request.user, is_deleted=False)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SocialAccountCreateSerializer
        return SocialAccountSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audit logs"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    
    def get_queryset(self):
        return AuditLog.objects.filter(actor=self.request.user).order_by('-created_at')


# Placeholder views for additional functionality
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        return Response({'message': 'Change password endpoint - to be implemented'})


class DeactivateAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        return Response({'message': 'Deactivate account endpoint - to be implemented'})


class ReactivateAccountView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        return Response({'message': 'Reactivate account endpoint - to be implemented'})


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        return Response({'message': 'Email verification endpoint - to be implemented'})


class ResendVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        return Response({'message': 'Resend verification endpoint - to be implemented'})


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        return Response({'message': 'Forgot password endpoint - to be implemented'})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        return Response({'message': 'Reset password endpoint - to be implemented'})