from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'actions', views.AdminActionViewSet)
router.register(r'configurations', views.SystemConfigurationViewSet)
router.register(r'metrics', views.PlatformMetricsViewSet)
router.register(r'templates', views.NotificationTemplateViewSet)
router.register(r'support-tickets', views.SupportTicketViewSet)

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Dashboard and overview
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('activity/', views.RecentActivityView.as_view(), name='recent_activity'),
    path('health/', views.SystemHealthView.as_view(), name='system_health'),
    
    # User management
    path('users/<uuid:user_id>/<str:action>/', views.UserManagementView.as_view(), name='user_management'),
    path('users/search/', views.UserSearchView.as_view(), name='user_search'),
    
    # Campaign management
    path('campaigns/<uuid:campaign_id>/<str:action>/', views.CampaignManagementView.as_view(), name='campaign_management'),
    path('campaigns/search/', views.CampaignSearchView.as_view(), name='campaign_search'),
    
    # Financial management
    path('withdrawals/<uuid:withdrawal_id>/<str:action>/', views.FinancialManagementView.as_view(), name='financial_management'),
    path('withdrawals/search/', views.WithdrawalSearchView.as_view(), name='withdrawal_search'),
    
    # System configuration
    path('config/', views.ConfigurationManagementView.as_view(), name='configuration_management'),
    
    # Bulk operations
    path('bulk/', views.BulkActionView.as_view(), name='bulk_action'),
]
