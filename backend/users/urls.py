from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'social-accounts', views.SocialAccountViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    
    # Password management
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    
    # KYC
    path('kyc/submit/', views.SubmitKYCView.as_view(), name='submit_kyc'),
    path('kyc/status/', views.KYCStatusView.as_view(), name='kyc_status'),
    
    # Social accounts
    path('', include(router.urls)),
    
    # Account management
    path('deactivate/', views.DeactivateAccountView.as_view(), name='deactivate_account'),
    path('reactivate/', views.ReactivateAccountView.as_view(), name='reactivate_account'),
]
