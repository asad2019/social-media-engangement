from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.SecurityEventViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'data-access-logs', views.DataAccessLogViewSet)

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Security monitoring
    path('monitoring/analysis/', views.SecurityAnalysisView.as_view(), name='security_analysis'),
    path('monitoring/anomalies/', views.AnomalyDetectionView.as_view(), name='anomaly_detection'),
    
    # Threat detection
    path('threats/ip/<str:ip_address>/', views.IPThreatAnalysisView.as_view(), name='ip_threat_analysis'),
    path('threats/block-ip/', views.BlockIPView.as_view(), name='block_ip'),
    
    # Compliance
    path('compliance/gdpr/<uuid:user_id>/', views.GDPRReportView.as_view(), name='gdpr_report'),
    path('compliance/anonymize/<uuid:user_id>/', views.AnonymizeUserView.as_view(), name='anonymize_user'),
    path('compliance/delete/<uuid:user_id>/', views.DeleteUserView.as_view(), name='delete_user'),
]
