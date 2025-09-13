from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.WalletTransactionViewSet)
router.register(r'withdrawals', views.WithdrawalViewSet)

urlpatterns = [
    # Wallet management
    path('', include(router.urls)),
    
    # Wallet balance and overview
    path('balance/', views.WalletBalanceView.as_view(), name='wallet_balance'),
    path('overview/', views.WalletOverviewView.as_view(), name='wallet_overview'),
    
    # Withdrawal management
    path('withdraw/', views.RequestWithdrawalView.as_view(), name='request_withdrawal'),
    path('withdrawals/<uuid:withdrawal_id>/cancel/', views.CancelWithdrawalView.as_view(), name='cancel_withdrawal'),
    
    # Transaction history
    path('transactions/export/', views.ExportTransactionsView.as_view(), name='export_transactions'),
    path('transactions/summary/', views.TransactionSummaryView.as_view(), name='transaction_summary'),
    
    # Payment methods
    path('payment-methods/', views.PaymentMethodViewSet.as_view({'get': 'list', 'post': 'create'}), name='payment_methods'),
    path('payment-methods/<uuid:method_id>/', views.PaymentMethodViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='payment_method_detail'),
    
    # Stripe Connect (for earners)
    path('stripe/connect/', views.StripeConnectView.as_view(), name='stripe_connect'),
    path('stripe/connect/status/', views.StripeConnectStatusView.as_view(), name='stripe_connect_status'),
    path('stripe/connect/disconnect/', views.StripeDisconnectView.as_view(), name='stripe_disconnect'),
    
    # Webhooks
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
]
