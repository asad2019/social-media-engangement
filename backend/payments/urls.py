from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StripeAccountViewSet, PaymentIntentViewSet, PayoutViewSet,
    TransferViewSet, WebhookEventViewSet, StripeWebhookView,
    PaymentMethodsView, PaymentStatsView
)

router = DefaultRouter()
router.register(r'stripe-accounts', StripeAccountViewSet)
router.register(r'payment-intents', PaymentIntentViewSet)
router.register(r'payouts', PayoutViewSet)
router.register(r'transfers', TransferViewSet)
router.register(r'webhook-events', WebhookEventViewSet)

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Webhook endpoint
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Additional endpoints
    path('payment-methods/', PaymentMethodsView.as_view(), name='payment-methods'),
    path('stats/', PaymentStatsView.as_view(), name='payment-stats'),
]
