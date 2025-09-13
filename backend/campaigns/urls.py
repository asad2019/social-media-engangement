from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.CampaignViewSet)
router.register(r'analytics', views.CampaignAnalyticsViewSet)

urlpatterns = [
    # Campaign management
    path('', include(router.urls)),
    
    # Campaign actions
    path('<uuid:campaign_id>/fund/', views.FundCampaignView.as_view(), name='fund_campaign'),
    path('<uuid:campaign_id>/pause/', views.PauseCampaignView.as_view(), name='pause_campaign'),
    path('<uuid:campaign_id>/resume/', views.ResumeCampaignView.as_view(), name='resume_campaign'),
    path('<uuid:campaign_id>/cancel/', views.CancelCampaignView.as_view(), name='cancel_campaign'),
    path('<uuid:campaign_id>/refund/', views.RefundCampaignView.as_view(), name='refund_campaign'),
    
    # Campaign preview and cost calculation
    path('preview/', views.CampaignPreviewView.as_view(), name='campaign_preview'),
    path('cost-calculator/', views.CostCalculatorView.as_view(), name='cost_calculator'),
    
    # Campaign analytics
    path('<uuid:campaign_id>/analytics/', views.CampaignAnalyticsDetailView.as_view(), name='campaign_analytics'),
    path('<uuid:campaign_id>/analytics/export/', views.ExportCampaignAnalyticsView.as_view(), name='export_analytics'),
    
    # Campaign templates
    path('templates/', views.CampaignTemplateViewSet.as_view({'get': 'list', 'post': 'create'}), name='campaign_templates'),
    path('templates/<uuid:template_id>/', views.CampaignTemplateViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='campaign_template_detail'),
]
