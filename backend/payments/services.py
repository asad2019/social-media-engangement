import stripe
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import Dict, Any, Optional
import uuid

from .models import StripeAccount, PaymentIntent, Payout, Transfer, WebhookEvent

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for handling Stripe operations"""
    
    def __init__(self):
        self.stripe = stripe
    
    def create_connect_account(self, user, account_type='express') -> StripeAccount:
        """Create a Stripe Connect account for a user"""
        try:
            # Create Stripe Connect account
            account = self.stripe.Account.create(
                type=account_type,
                country='US',  # Default to US, should be configurable
                email=user.email,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                }
            )
            
            # Create local record
            stripe_account = StripeAccount.objects.create(
                user=user,
                stripe_account_id=account.id,
                account_type=account_type,
                status='pending',
                charges_enabled=account.charges_enabled,
                payouts_enabled=account.payouts_enabled,
                details_submitted=account.details_submitted,
                requirements=account.requirements,
                metadata=account.metadata,
            )
            
            logger.info(f"Created Stripe Connect account {account.id} for user {user.id}")
            return stripe_account
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating Connect account: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Connect account: {e}")
            raise
    
    def create_account_link(self, stripe_account: StripeAccount, refresh_url: str, return_url: str) -> str:
        """Create account link for onboarding"""
        try:
            account_link = self.stripe.AccountLink.create(
                account=stripe_account.stripe_account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type='account_onboarding',
            )
            
            return account_link.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account link: {e}")
            raise
    
    def create_payment_intent(self, user, amount: Decimal, currency: str = 'usd', 
                            description: str = '', campaign=None, metadata: Dict = None) -> PaymentIntent:
        """Create a payment intent for funding campaigns or other payments"""
        try:
            # Convert to cents for Stripe
            amount_cents = int(amount * 100)
            
            # Create Stripe Payment Intent
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                description=description,
                metadata={
                    'user_id': str(user.id),
                    'campaign_id': str(campaign.id) if campaign else '',
                    **(metadata or {})
                },
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            # Create local record
            payment_intent = PaymentIntent.objects.create(
                user=user,
                stripe_payment_intent_id=intent.id,
                stripe_client_secret=intent.client_secret,
                amount=amount,
                currency=currency,
                description=description,
                status=intent.status,
                campaign=campaign,
                metadata=intent.metadata,
            )
            
            logger.info(f"Created payment intent {intent.id} for user {user.id}")
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {e}")
            raise
    
    def confirm_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """Confirm a payment intent"""
        try:
            # Get local record
            payment_intent = PaymentIntent.objects.get(stripe_payment_intent_id=payment_intent_id)
            
            # Confirm with Stripe
            intent = self.stripe.PaymentIntent.confirm(payment_intent_id)
            
            # Update local record
            payment_intent.status = intent.status
            payment_intent.updated_at = timezone.now()
            if intent.status == 'succeeded':
                payment_intent.succeeded_at = timezone.now()
            payment_intent.save()
            
            logger.info(f"Confirmed payment intent {payment_intent_id}")
            return payment_intent
            
        except PaymentIntent.DoesNotExist:
            logger.error(f"Payment intent {payment_intent_id} not found")
            raise ValueError("Payment intent not found")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment intent: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error confirming payment intent: {e}")
            raise
    
    def create_payout(self, withdrawal) -> Payout:
        """Create a payout for user withdrawal"""
        try:
            # Get user's Stripe account
            stripe_account = StripeAccount.objects.get(user=withdrawal.user)
            
            if not stripe_account.is_fully_setup():
                raise ValueError("Stripe account not fully set up")
            
            # Convert to cents
            amount_cents = int(withdrawal.net_amount * 100)
            
            # Create Stripe Payout
            payout = self.stripe.Payout.create(
                amount=amount_cents,
                currency='usd',
                destination=stripe_account.stripe_account_id,
                metadata={
                    'withdrawal_id': str(withdrawal.id),
                    'user_id': str(withdrawal.user.id),
                }
            )
            
            # Create local record
            stripe_payout = Payout.objects.create(
                user=withdrawal.user,
                withdrawal=withdrawal,
                stripe_payout_id=payout.id,
                amount=withdrawal.net_amount,
                currency='usd',
                arrival_date=timezone.datetime.fromtimestamp(payout.arrival_date) if payout.arrival_date else None,
                status=payout.status,
                metadata=payout.metadata,
            )
            
            logger.info(f"Created payout {payout.id} for withdrawal {withdrawal.id}")
            return stripe_payout
            
        except StripeAccount.DoesNotExist:
            logger.error(f"Stripe account not found for user {withdrawal.user.id}")
            raise ValueError("Stripe account not found")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payout: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating payout: {e}")
            raise
    
    def create_transfer(self, amount: Decimal, destination_account: str, 
                      reference: str, description: str, metadata: Dict = None) -> Transfer:
        """Create a transfer to a connected account"""
        try:
            # Convert to cents
            amount_cents = int(amount * 100)
            
            # Create Stripe Transfer
            transfer = self.stripe.Transfer.create(
                amount=amount_cents,
                currency='usd',
                destination=destination_account,
                metadata={
                    'reference': reference,
                    **(metadata or {})
                }
            )
            
            # Create local record
            stripe_transfer = Transfer.objects.create(
                stripe_transfer_id=transfer.id,
                amount=amount,
                currency='usd',
                destination_account=destination_account,
                reference=reference,
                description=description,
                status=transfer.status,
                metadata=transfer.metadata,
            )
            
            logger.info(f"Created transfer {transfer.id} for {reference}")
            return stripe_transfer
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating transfer: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating transfer: {e}")
            raise
    
    def refund_payment_intent(self, payment_intent_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """Refund a payment intent"""
        try:
            # Get local record
            payment_intent = PaymentIntent.objects.get(stripe_payment_intent_id=payment_intent_id)
            
            if not payment_intent.can_be_refunded():
                raise ValueError("Payment intent cannot be refunded")
            
            # Convert to cents if amount specified
            amount_cents = int(amount * 100) if amount else None
            
            # Create refund
            refund = self.stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=amount_cents,
                metadata={
                    'payment_intent_id': payment_intent_id,
                    'user_id': str(payment_intent.user.id),
                }
            )
            
            logger.info(f"Created refund {refund.id} for payment intent {payment_intent_id}")
            return {
                'refund_id': refund.id,
                'amount': Decimal(refund.amount) / 100,
                'status': refund.status,
            }
            
        except PaymentIntent.DoesNotExist:
            logger.error(f"Payment intent {payment_intent_id} not found")
            raise ValueError("Payment intent not found")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating refund: {e}")
            raise
    
    def get_account_balance(self, stripe_account_id: str) -> Dict[str, Any]:
        """Get account balance for a connected account"""
        try:
            balance = self.stripe.Balance.retrieve(stripe_account_id)
            
            return {
                'available': [{'amount': Decimal(b['amount']) / 100, 'currency': b['currency']} for b in balance.available],
                'pending': [{'amount': Decimal(b['amount']) / 100, 'currency': b['currency']} for b in balance.pending],
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting account balance: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting account balance: {e}")
            raise
    
    def sync_account_status(self, stripe_account: StripeAccount) -> StripeAccount:
        """Sync account status from Stripe"""
        try:
            account = self.stripe.Account.retrieve(stripe_account.stripe_account_id)
            
            # Update local record
            stripe_account.status = 'active' if account.charges_enabled and account.payouts_enabled else 'pending'
            stripe_account.charges_enabled = account.charges_enabled
            stripe_account.payouts_enabled = account.payouts_enabled
            stripe_account.details_submitted = account.details_submitted
            stripe_account.requirements = account.requirements
            stripe_account.updated_at = timezone.now()
            stripe_account.save()
            
            logger.info(f"Synced account status for {stripe_account.stripe_account_id}")
            return stripe_account
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error syncing account status: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error syncing account status: {e}")
            raise


class WebhookService:
    """Service for handling Stripe webhooks"""
    
    def __init__(self):
        self.stripe = stripe
    
    def process_webhook_event(self, event_data: Dict[str, Any]) -> WebhookEvent:
        """Process a Stripe webhook event"""
        try:
            # Create webhook event record
            webhook_event = WebhookEvent.objects.create(
                stripe_event_id=event_data['id'],
                event_type=event_data['type'],
                data=event_data,
            )
            
            # Process based on event type
            if event_data['type'] == 'account.updated':
                self._handle_account_updated(event_data)
            elif event_data['type'] == 'payment_intent.succeeded':
                self._handle_payment_intent_succeeded(event_data)
            elif event_data['type'] == 'payment_intent.payment_failed':
                self._handle_payment_intent_failed(event_data)
            elif event_data['type'] == 'payout.paid':
                self._handle_payout_paid(event_data)
            elif event_data['type'] == 'payout.failed':
                self._handle_payout_failed(event_data)
            elif event_data['type'] == 'transfer.created':
                self._handle_transfer_created(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_data['type']}")
            
            # Mark as processed
            webhook_event.mark_processed()
            
            return webhook_event
            
        except Exception as e:
            logger.error(f"Error processing webhook event {event_data.get('id', 'unknown')}: {e}")
            if 'webhook_event' in locals():
                webhook_event.mark_processed(error=str(e))
            raise
    
    def _handle_account_updated(self, event_data: Dict[str, Any]):
        """Handle account.updated webhook"""
        account_data = event_data['data']['object']
        
        try:
            stripe_account = StripeAccount.objects.get(stripe_account_id=account_data['id'])
            stripe_service = StripeService()
            stripe_service.sync_account_status(stripe_account)
        except StripeAccount.DoesNotExist:
            logger.warning(f"Stripe account {account_data['id']} not found for webhook")
    
    def _handle_payment_intent_succeeded(self, event_data: Dict[str, Any]):
        """Handle payment_intent.succeeded webhook"""
        payment_intent_data = event_data['data']['object']
        
        try:
            payment_intent = PaymentIntent.objects.get(stripe_payment_intent_id=payment_intent_data['id'])
            payment_intent.status = 'succeeded'
            payment_intent.succeeded_at = timezone.now()
            payment_intent.save()
            
            # Create wallet transaction
            from wallets.models import WalletTransaction
            WalletTransaction.create_transaction(
                user=payment_intent.user,
                transaction_type='credit',
                amount=payment_intent.amount,
                reference=f"stripe_payment_{payment_intent.stripe_payment_intent_id}",
                description=f"Payment received: {payment_intent.description}",
                metadata={
                    'payment_intent_id': payment_intent.stripe_payment_intent_id,
                    'stripe_payment_intent_id': payment_intent.stripe_payment_intent_id,
                }
            )
            
        except PaymentIntent.DoesNotExist:
            logger.warning(f"Payment intent {payment_intent_data['id']} not found for webhook")
    
    def _handle_payment_intent_failed(self, event_data: Dict[str, Any]):
        """Handle payment_intent.payment_failed webhook"""
        payment_intent_data = event_data['data']['object']
        
        try:
            payment_intent = PaymentIntent.objects.get(stripe_payment_intent_id=payment_intent_data['id'])
            payment_intent.status = 'failed'
            payment_intent.save()
        except PaymentIntent.DoesNotExist:
            logger.warning(f"Payment intent {payment_intent_data['id']} not found for webhook")
    
    def _handle_payout_paid(self, event_data: Dict[str, Any]):
        """Handle payout.paid webhook"""
        payout_data = event_data['data']['object']
        
        try:
            payout = Payout.objects.get(stripe_payout_id=payout_data['id'])
            payout.status = 'paid'
            payout.save()
            
            # Update withdrawal status
            payout.withdrawal.complete(
                payment_provider_id=payout.stripe_payout_id,
                transaction_id=payout.stripe_payout_id
            )
            
        except Payout.DoesNotExist:
            logger.warning(f"Payout {payout_data['id']} not found for webhook")
    
    def _handle_payout_failed(self, event_data: Dict[str, Any]):
        """Handle payout.failed webhook"""
        payout_data = event_data['data']['object']
        
        try:
            payout = Payout.objects.get(stripe_payout_id=payout_data['id'])
            payout.status = 'failed'
            payout.failure_code = payout_data.get('failure_code', '')
            payout.failure_message = payout_data.get('failure_message', '')
            payout.save()
            
            # Update withdrawal status
            payout.withdrawal.fail(
                reason=f"Stripe payout failed: {payout.failure_message}"
            )
            
        except Payout.DoesNotExist:
            logger.warning(f"Payout {payout_data['id']} not found for webhook")
    
    def _handle_transfer_created(self, event_data: Dict[str, Any]):
        """Handle transfer.created webhook"""
        transfer_data = event_data['data']['object']
        
        try:
            transfer = Transfer.objects.get(stripe_transfer_id=transfer_data['id'])
            transfer.status = transfer_data['status']
            transfer.save()
        except Transfer.DoesNotExist:
            logger.warning(f"Transfer {transfer_data['id']} not found for webhook")
