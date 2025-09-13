from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import stripe
from django.conf import settings

from .models import StripeAccount, PaymentIntent, Payout, Transfer, WebhookEvent
from .serializers import (
    StripeAccountSerializer, StripeAccountCreateSerializer, AccountLinkSerializer,
    PaymentIntentSerializer, PaymentIntentCreateSerializer, PaymentIntentConfirmSerializer,
    PayoutSerializer, PayoutCreateSerializer,
    TransferSerializer, TransferCreateSerializer,
    RefundSerializer, AccountBalanceSerializer, WebhookEventSerializer
)
from .services import StripeService, WebhookService


class StripeAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for Stripe Connect accounts"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = StripeAccount.objects.all()
    
    def get_queryset(self):
        return StripeAccount.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StripeAccountCreateSerializer
        return StripeAccountSerializer
    
    @action(detail=True, methods=['post'])
    def create_account_link(self, request, pk=None):
        """Create account link for onboarding"""
        stripe_account = self.get_object()
        
        serializer = AccountLinkSerializer(
            data=request.data,
            context={'stripe_account': stripe_account}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_status(self, request, pk=None):
        """Sync account status from Stripe"""
        stripe_account = self.get_object()
        
        try:
            stripe_service = StripeService()
            updated_account = stripe_service.sync_account_status(stripe_account)
            
            serializer = StripeAccountSerializer(updated_account)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get account balance"""
        stripe_account = self.get_object()
        
        try:
            stripe_service = StripeService()
            balance = stripe_service.get_account_balance(stripe_account.stripe_account_id)
            
            serializer = AccountBalanceSerializer(balance)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentIntentViewSet(viewsets.ModelViewSet):
    """ViewSet for payment intents"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = PaymentIntent.objects.all()
    
    def get_queryset(self):
        return PaymentIntent.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentIntentCreateSerializer
        elif self.action == 'confirm':
            return PaymentIntentConfirmSerializer
        return PaymentIntentSerializer
    
    @action(detail=False, methods=['post'])
    def confirm(self, request):
        """Confirm a payment intent"""
        serializer = PaymentIntentConfirmSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                payment_intent = serializer.save()
                response_serializer = PaymentIntentSerializer(payment_intent)
                return Response(response_serializer.data)
                
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Refund a payment intent"""
        payment_intent = self.get_object()
        
        serializer = RefundSerializer(
            data={
                'payment_intent_id': payment_intent.stripe_payment_intent_id,
                'amount': request.data.get('amount')
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                refund_data = serializer.save()
                return Response(refund_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayoutViewSet(viewsets.ModelViewSet):
    """ViewSet for payouts"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payout.objects.all()
    
    def get_queryset(self):
        return Payout.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PayoutCreateSerializer
        return PayoutSerializer


class TransferViewSet(viewsets.ModelViewSet):
    """ViewSet for transfers (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Transfer.objects.all()
    
    def get_queryset(self):
        # Only admins can see all transfers
        if self.request.user.role in ['admin', 'moderator']:
            return Transfer.objects.all()
        return Transfer.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransferCreateSerializer
        return TransferSerializer


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for webhook events (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    
    def get_queryset(self):
        # Only admins can see webhook events
        if self.request.user.role in ['admin', 'moderator']:
            return WebhookEvent.objects.all()
        return WebhookEvent.objects.none()


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Handle Stripe webhooks"""
    permission_classes = []  # No authentication required for webhooks
    
    def post(self, request):
        """Process Stripe webhook"""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Process the event
            webhook_service = WebhookService()
            webhook_event = webhook_service.process_webhook_event(event)
            
            return HttpResponse(status=200)
            
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)
        except Exception as e:
            return HttpResponse(status=500)


class PaymentMethodsView(APIView):
    """View for payment methods"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get available payment methods"""
        # This would typically return available payment methods
        # For now, return a simple list
        payment_methods = [
            {
                'id': 'card',
                'name': 'Credit/Debit Card',
                'type': 'card',
                'enabled': True
            },
            {
                'id': 'bank_transfer',
                'name': 'Bank Transfer',
                'type': 'bank_transfer',
                'enabled': True
            },
            {
                'id': 'paypal',
                'name': 'PayPal',
                'type': 'paypal',
                'enabled': False  # Not implemented yet
            }
        ]
        
        return Response(payment_methods)


class PaymentStatsView(APIView):
    """View for payment statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get payment statistics for user"""
        user = request.user
        
        # Get payment statistics
        total_payments = PaymentIntent.objects.filter(
            user=user,
            status='succeeded'
        ).count()
        
        total_amount = sum(
            PaymentIntent.objects.filter(
                user=user,
                status='succeeded'
            ).values_list('amount', flat=True)
        )
        
        total_payouts = Payout.objects.filter(
            user=user,
            status='paid'
        ).count()
        
        total_payout_amount = sum(
            Payout.objects.filter(
                user=user,
                status='paid'
            ).values_list('amount', flat=True)
        )
        
        stats = {
            'total_payments': total_payments,
            'total_payment_amount': float(total_amount),
            'total_payouts': total_payouts,
            'total_payout_amount': float(total_payout_amount),
            'current_balance': float(user.wallet_balance),
        }
        
        return Response(stats)