from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.core.paginator import Paginator
from decimal import Decimal

from .models import WalletTransaction, Withdrawal
from .serializers import (
    WalletTransactionSerializer, WithdrawalSerializer, WithdrawalCreateSerializer,
    WalletBalanceSerializer, TransactionHistorySerializer, WithdrawalStatsSerializer,
    AdminWithdrawalSerializer, AdminWithdrawalUpdateSerializer, BulkWithdrawalSerializer
)
from users.permissions import IsEarner, IsAdmin
from payments.services import StripeService


class WalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for wallet transactions"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = WalletTransaction.objects.all()
    serializer_class = WalletTransactionSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return WalletTransaction.objects.all()
        else:
            return WalletTransaction.objects.filter(user=user)


class WithdrawalViewSet(viewsets.ModelViewSet):
    """ViewSet for withdrawals"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Withdrawal.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WithdrawalCreateSerializer
        elif self.action in ['update', 'partial_update'] and self.request.user.is_staff:
            return AdminWithdrawalUpdateSerializer
        elif self.request.user.is_staff:
            return AdminWithdrawalSerializer
        return WithdrawalSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Withdrawal.objects.all()
        else:
            return Withdrawal.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        """Approve a withdrawal"""
        withdrawal = self.get_object()
        
        if withdrawal.status != 'pending':
            return Response({'error': 'Only pending withdrawals can be approved'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Update withdrawal status
                withdrawal.status = 'processing'
                withdrawal.admin_notes = request.data.get('admin_notes', '')
                withdrawal.save()
                
                # Process payment through Stripe
                stripe_service = StripeService()
                payout = stripe_service.create_payout(
                    user=withdrawal.user,
                    amount=withdrawal.net_amount,
                    metadata={'withdrawal_id': str(withdrawal.id)}
                )
                
                if payout:
                    withdrawal.payment_provider_id = payout.id
                    withdrawal.save()
                
                return Response({'message': 'Withdrawal approved and processing'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        """Reject a withdrawal"""
        withdrawal = self.get_object()
        
        if withdrawal.status != 'pending':
            return Response({'error': 'Only pending withdrawals can be rejected'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Update withdrawal status
                withdrawal.status = 'failed'
                withdrawal.failure_reason = request.data.get('failure_reason', '')
                withdrawal.admin_notes = request.data.get('admin_notes', '')
                withdrawal.save()
                
                # Refund the amount to user's wallet
                WalletTransaction.objects.create(
                    user=withdrawal.user,
                    transaction_type='refund',
                    amount=withdrawal.amount,
                    balance_before=withdrawal.user.wallet_balance,
                    balance_after=withdrawal.user.wallet_balance + withdrawal.amount,
                    reference=f'WITHDRAWAL_REFUND_{withdrawal.id}',
                    description=f'Refund for rejected withdrawal',
                    metadata={'withdrawal_id': str(withdrawal.id)}
                )
                
                # Update user balance
                withdrawal.user.wallet_balance += withdrawal.amount
                withdrawal.user.save()
                
                return Response({'message': 'Withdrawal rejected and amount refunded'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def complete(self, request, pk=None):
        """Mark withdrawal as completed"""
        withdrawal = self.get_object()
        
        if withdrawal.status != 'processing':
            return Response({'error': 'Only processing withdrawals can be completed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        withdrawal.status = 'completed'
        withdrawal.processed_at = timezone.now()
        withdrawal.save()
        
        return Response({'message': 'Withdrawal marked as completed'}, 
                      status=status.HTTP_200_OK)


class WalletBalanceView(APIView):
    """Get wallet balance and statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Calculate pending withdrawals
        pending_withdrawals = Withdrawal.objects.filter(
            user=user,
            status__in=['pending', 'processing']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate total earned
        total_earned = WalletTransaction.objects.filter(
            user=user,
            transaction_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate total withdrawn
        total_withdrawn = Withdrawal.objects.filter(
            user=user,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        available_balance = user.wallet_balance - pending_withdrawals
        
        data = {
            'balance': user.wallet_balance,
            'pending_withdrawals': pending_withdrawals,
            'available_balance': available_balance,
            'total_earned': total_earned,
            'total_withdrawn': total_withdrawn
        }
        
        serializer = WalletBalanceSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TransactionHistoryView(APIView):
    """Get transaction history with pagination"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        transaction_type = request.query_params.get('type')
        
        # Base queryset
        transactions = WalletTransaction.objects.filter(user=user)
        
        # Filter by transaction type
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Order by created_at descending
        transactions = transactions.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(transactions, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = WalletTransactionSerializer(page_obj.object_list, many=True)
        
        data = {
            'transactions': serializer.data,
            'total_count': paginator.count,
            'page': page,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        }
        
        serializer = TransactionHistorySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WithdrawalStatsView(APIView):
    """Get withdrawal statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Calculate statistics
        total_withdrawals = Withdrawal.objects.filter(user=user).count()
        pending_withdrawals = Withdrawal.objects.filter(user=user, status='pending').count()
        completed_withdrawals = Withdrawal.objects.filter(user=user, status='completed').count()
        failed_withdrawals = Withdrawal.objects.filter(user=user, status='failed').count()
        
        total_amount_withdrawn = Withdrawal.objects.filter(
            user=user,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        avg_withdrawal_amount = Withdrawal.objects.filter(
            user=user,
            status='completed'
        ).aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
        
        # Calculate success rate
        total_processed = completed_withdrawals + failed_withdrawals
        withdrawal_success_rate = 0
        if total_processed > 0:
            withdrawal_success_rate = round((completed_withdrawals / total_processed) * 100, 2)
        
        data = {
            'total_withdrawals': total_withdrawals,
            'pending_withdrawals': pending_withdrawals,
            'completed_withdrawals': completed_withdrawals,
            'failed_withdrawals': failed_withdrawals,
            'total_amount_withdrawn': total_amount_withdrawn,
            'avg_withdrawal_amount': avg_withdrawal_amount,
            'withdrawal_success_rate': withdrawal_success_rate
        }
        
        serializer = WithdrawalStatsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminWithdrawalManagementView(APIView):
    """Admin view for managing withdrawals"""
    permission_classes = [IsAdmin]
    
    def get(self, request):
        """Get all withdrawals with filters"""
        status_filter = request.query_params.get('status')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        withdrawals = Withdrawal.objects.all().order_by('-created_at')
        
        if status_filter:
            withdrawals = withdrawals.filter(status=status_filter)
        
        paginator = Paginator(withdrawals, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = AdminWithdrawalSerializer(page_obj.object_list, many=True)
        
        return Response({
            'withdrawals': serializer.data,
            'total_count': paginator.count,
            'page': page,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Bulk operations on withdrawals"""
        serializer = BulkWithdrawalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        withdrawal_ids = data['withdrawal_ids']
        action = data['action']
        admin_notes = data.get('admin_notes', '')
        
        try:
            with transaction.atomic():
                withdrawals = Withdrawal.objects.filter(id__in=withdrawal_ids)
                
                if action == 'approve':
                    withdrawals.update(status='processing', admin_notes=admin_notes)
                elif action == 'reject':
                    withdrawals.update(status='failed', admin_notes=admin_notes)
                elif action == 'process':
                    withdrawals.update(status='processing', admin_notes=admin_notes)
                
                return Response({'message': f'{len(withdrawal_ids)} withdrawals {action}d successfully'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletStatsView(APIView):
    """Get platform-wide wallet statistics"""
    permission_classes = [IsAdmin]
    
    def get(self, request):
        stats = {
            'total_wallet_balance': WalletTransaction.objects.filter(
                transaction_type='credit'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            
            'total_hold_amount': WalletTransaction.objects.filter(
                transaction_type='hold'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            
            'total_withdrawals': Withdrawal.objects.filter(
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            
            'pending_withdrawals': Withdrawal.objects.filter(
                status__in=['pending', 'processing']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            
            'total_transactions': WalletTransaction.objects.count(),
            'total_withdrawal_requests': Withdrawal.objects.count(),
            
            'avg_transaction_amount': WalletTransaction.objects.aggregate(
                avg=Avg('amount')
            )['avg'] or Decimal('0.00'),
            
            'avg_withdrawal_amount': Withdrawal.objects.aggregate(
                avg=Avg('amount')
            )['avg'] or Decimal('0.00')
        }
        
        return Response(stats, status=status.HTTP_200_OK)