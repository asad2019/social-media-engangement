from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rules', views.VerificationRuleViewSet)
router.register(r'sessions', views.VerificationSessionViewSet)
router.register(r'manual-review', views.ManualReviewQueueViewSet)
router.register(r'fraud-detection', views.FraudDetectionViewSet)
router.register(r'fraud-alerts', views.FraudAlertViewSet)

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Statistics and health
    path('stats/', views.VerificationStatsView.as_view(), name='verification_stats'),
    path('health/', views.VerificationHealthView.as_view(), name='verification_health'),
    
    # User fraud analysis
    path('fraud-analysis/<uuid:user_id>/', views.UserFraudAnalysisView.as_view(), name='user_fraud_analysis'),
    
    # Testing
    path('test/', views.VerificationTestView.as_view(), name='verification_test'),
]
