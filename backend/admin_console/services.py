import logging
from typing import Dict, Any, List, Optional
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from .models import AdminAction, SystemConfiguration, PlatformMetrics, NotificationTemplate, SupportTicket
from users.models import User
from campaigns.models import Campaign
from jobs.models import Job, JobAttempt
from wallets.models import WalletTransaction, Withdrawal
from verification.models import ManualReviewQueue, FraudAlert

logger = logging.getLogger(__name__)


class AdminDashboardService:
    """Service for admin dashboard data and metrics"""
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get comprehensive dashboard overview"""
        try:
            # Date ranges
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # User metrics
            total_users = User.objects.count()
            active_users = User.objects.filter(
                last_login__gte=week_ago
            ).count()
            new_users_today = User.objects.filter(
                date_joined__date=today
            ).count()
            new_users_week = User.objects.filter(
                date_joined__gte=week_ago
            ).count()
            
            # Campaign metrics
            total_campaigns = Campaign.objects.count()
            active_campaigns = Campaign.objects.filter(
                status='active'
            ).count()
            campaigns_today = Campaign.objects.filter(
                created_at__date=today
            ).count()
            
            # Job metrics
            total_jobs = Job.objects.count()
            completed_jobs = Job.objects.filter(
                status='completed'
            ).count()
            pending_jobs = Job.objects.filter(
                status='pending'
            ).count()
            
            # Financial metrics
            total_transactions = WalletTransaction.objects.count()
            total_volume = WalletTransaction.objects.filter(
                transaction_type='credit'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Pending items
            pending_reviews = ManualReviewQueue.objects.filter(
                status='pending'
            ).count()
            active_fraud_alerts = FraudAlert.objects.filter(
                status='active'
            ).count()
            pending_withdrawals = Withdrawal.objects.filter(
                status='pending'
            ).count()
            
            return {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'new_today': new_users_today,
                    'new_week': new_users_week,
                    'growth_rate': self._calculate_growth_rate(new_users_week, 7)
                },
                'campaigns': {
                    'total': total_campaigns,
                    'active': active_campaigns,
                    'created_today': campaigns_today,
                    'completion_rate': self._calculate_completion_rate()
                },
                'jobs': {
                    'total': total_jobs,
                    'completed': completed_jobs,
                    'pending': pending_jobs,
                    'success_rate': self._calculate_job_success_rate()
                },
                'financial': {
                    'total_transactions': total_transactions,
                    'total_volume': float(total_volume),
                    'pending_withdrawals': pending_withdrawals,
                    'platform_revenue': self._calculate_platform_revenue()
                },
                'moderation': {
                    'pending_reviews': pending_reviews,
                    'active_fraud_alerts': active_fraud_alerts,
                    'escalated_items': self._get_escalated_items_count()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard overview: {e}")
            return {}
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent platform activity"""
        try:
            activities = []
            
            # Recent user registrations
            recent_users = User.objects.order_by('-date_joined')[:5]
            for user in recent_users:
                activities.append({
                    'type': 'user_registration',
                    'timestamp': user.date_joined,
                    'description': f"New user registered: {user.username}",
                    'user_id': str(user.id),
                    'severity': 'info'
                })
            
            # Recent campaigns
            recent_campaigns = Campaign.objects.order_by('-created_at')[:5]
            for campaign in recent_campaigns:
                activities.append({
                    'type': 'campaign_created',
                    'timestamp': campaign.created_at,
                    'description': f"Campaign created: {campaign.title}",
                    'campaign_id': str(campaign.id),
                    'severity': 'info'
                })
            
            # Recent fraud alerts
            recent_alerts = FraudAlert.objects.filter(
                status='active'
            ).order_by('-created_at')[:5]
            for alert in recent_alerts:
                activities.append({
                    'type': 'fraud_alert',
                    'timestamp': alert.created_at,
                    'description': f"Fraud alert: {alert.description}",
                    'alert_id': str(alert.id),
                    'severity': 'high'
                })
            
            # Recent admin actions
            recent_actions = AdminAction.objects.order_by('-performed_at')[:5]
            for action in recent_actions:
                activities.append({
                    'type': 'admin_action',
                    'timestamp': action.performed_at,
                    'description': f"Admin action: {action.description}",
                    'action_id': str(action.id),
                    'severity': 'medium'
                })
            
            # Sort by timestamp and return limited results
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Check database connectivity
            db_healthy = True
            try:
                User.objects.count()
            except:
                db_healthy = False
            
            # Check Redis connectivity
            redis_healthy = True
            try:
                from django.core.cache import cache
                cache.set('health_check', 'ok', 10)
                redis_healthy = cache.get('health_check') == 'ok'
            except:
                redis_healthy = False
            
            # Check ML service
            ml_service_healthy = True
            try:
                import httpx
                import asyncio
                
                async def check_ml_service():
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.get(
                                f"{settings.ML_SERVICE_URL}/health",
                                timeout=5.0
                            )
                            return response.status_code == 200
                    except:
                        return False
                
                ml_service_healthy = asyncio.run(check_ml_service())
            except:
                ml_service_healthy = False
            
            # Calculate overall health score
            health_checks = [db_healthy, redis_healthy, ml_service_healthy]
            health_score = sum(health_checks) / len(health_checks) * 100
            
            return {
                'overall_health': health_score,
                'services': {
                    'database': db_healthy,
                    'redis': redis_healthy,
                    'ml_service': ml_service_healthy
                },
                'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical'
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {'overall_health': 0, 'status': 'unknown'}
    
    def _calculate_growth_rate(self, new_users: int, days: int) -> float:
        """Calculate user growth rate"""
        try:
            previous_period = User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=days*2),
                date_joined__lt=timezone.now() - timedelta(days=days)
            ).count()
            
            if previous_period == 0:
                return 0.0
            
            growth_rate = ((new_users - previous_period) / previous_period) * 100
            return round(growth_rate, 2)
        except:
            return 0.0
    
    def _calculate_completion_rate(self) -> float:
        """Calculate campaign completion rate"""
        try:
            total_campaigns = Campaign.objects.count()
            if total_campaigns == 0:
                return 0.0
            
            completed_campaigns = Campaign.objects.filter(
                status='completed'
            ).count()
            
            return round((completed_campaigns / total_campaigns) * 100, 2)
        except:
            return 0.0
    
    def _calculate_job_success_rate(self) -> float:
        """Calculate job success rate"""
        try:
            total_jobs = Job.objects.count()
            if total_jobs == 0:
                return 0.0
            
            successful_jobs = Job.objects.filter(
                status='completed'
            ).count()
            
            return round((successful_jobs / total_jobs) * 100, 2)
        except:
            return 0.0
    
    def _calculate_platform_revenue(self) -> float:
        """Calculate platform revenue from commissions"""
        try:
            commission_transactions = WalletTransaction.objects.filter(
                transaction_type='commission'
            )
            total_commission = commission_transactions.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            return float(total_commission)
        except:
            return 0.0
    
    def _get_escalated_items_count(self) -> int:
        """Get count of escalated items requiring attention"""
        try:
            escalated_count = 0
            
            # High priority manual reviews
            escalated_count += ManualReviewQueue.objects.filter(
                priority='high',
                status='pending'
            ).count()
            
            # High severity fraud alerts
            escalated_count += FraudAlert.objects.filter(
                severity='high',
                status='active'
            ).count()
            
            # Large withdrawal requests
            escalated_count += Withdrawal.objects.filter(
                amount__gte=Decimal('1000'),
                status='pending'
            ).count()
            
            return escalated_count
        except:
            return 0


class UserManagementService:
    """Service for user management operations"""
    
    def suspend_user(self, user: User, admin: User, reason: str, duration_days: int = None) -> bool:
        """Suspend a user"""
        try:
            user.is_active = False
            user.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='user_suspend',
                target_type='User',
                target_id=user.id,
                target_description=f"User: {user.username}",
                description=f"User suspended: {user.username}",
                reason=reason,
                metadata={
                    'duration_days': duration_days,
                    'suspended_at': timezone.now().isoformat()
                }
            )
            
            logger.info(f"User {user.username} suspended by {admin.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to suspend user {user.id}: {e}")
            return False
    
    def ban_user(self, user: User, admin: User, reason: str) -> bool:
        """Ban a user permanently"""
        try:
            user.is_active = False
            user.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='user_ban',
                target_type='User',
                target_id=user.id,
                target_description=f"User: {user.username}",
                description=f"User banned: {user.username}",
                reason=reason,
                metadata={
                    'banned_at': timezone.now().isoformat()
                }
            )
            
            logger.info(f"User {user.username} banned by {admin.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ban user {user.id}: {e}")
            return False
    
    def verify_user(self, user: User, admin: User, reason: str = '') -> bool:
        """Verify a user's KYC"""
        try:
            user.kyc_status = 'verified'
            user.is_verified = True
            user.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='user_verify',
                target_type='User',
                target_id=user.id,
                target_description=f"User: {user.username}",
                description=f"User verified: {user.username}",
                reason=reason
            )
            
            logger.info(f"User {user.username} verified by {admin.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify user {user.id}: {e}")
            return False
    
    def adjust_wallet(self, user: User, admin: User, amount: Decimal, reason: str) -> bool:
        """Adjust user's wallet balance"""
        try:
            from wallets.models import WalletTransaction
            
            # Create wallet transaction
            WalletTransaction.create_transaction(
                user=user,
                transaction_type='credit' if amount > 0 else 'debit',
                amount=amount,
                reference=f"admin_adjustment_{admin.id}",
                description=f"Admin wallet adjustment: {reason}",
                metadata={
                    'admin_id': str(admin.id),
                    'admin_username': admin.username,
                    'adjustment_reason': reason
                }
            )
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='wallet_adjust',
                target_type='User',
                target_id=user.id,
                target_description=f"User: {user.username}",
                description=f"Wallet adjusted for {user.username}: {amount}",
                reason=reason,
                metadata={
                    'amount': str(amount),
                    'new_balance': str(user.wallet_balance)
                }
            )
            
            logger.info(f"Wallet adjusted for {user.username} by {admin.username}: {amount}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to adjust wallet for user {user.id}: {e}")
            return False


class CampaignManagementService:
    """Service for campaign management operations"""
    
    def pause_campaign(self, campaign: Campaign, admin: User, reason: str) -> bool:
        """Pause a campaign"""
        try:
            campaign.status = 'paused'
            campaign.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='campaign_pause',
                target_type='Campaign',
                target_id=campaign.id,
                target_description=f"Campaign: {campaign.title}",
                description=f"Campaign paused: {campaign.title}",
                reason=reason
            )
            
            logger.info(f"Campaign {campaign.title} paused by {admin.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause campaign {campaign.id}: {e}")
            return False
    
    def cancel_campaign(self, campaign: Campaign, admin: User, reason: str) -> bool:
        """Cancel a campaign and refund"""
        try:
            campaign.status = 'cancelled'
            campaign.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='campaign_cancel',
                target_type='Campaign',
                target_id=campaign.id,
                target_description=f"Campaign: {campaign.title}",
                description=f"Campaign cancelled: {campaign.title}",
                reason=reason
            )
            
            logger.info(f"Campaign {campaign.title} cancelled by {admin.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel campaign {campaign.id}: {e}")
            return False


class FinancialManagementService:
    """Service for financial management operations"""
    
    def approve_withdrawal(self, withdrawal: Withdrawal, admin: User, notes: str = '') -> bool:
        """Approve a withdrawal"""
        try:
            withdrawal.status = 'processing'
            withdrawal.processed_by = admin
            withdrawal.processed_at = timezone.now()
            withdrawal.admin_notes = notes
            withdrawal.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='withdrawal_approve',
                target_type='Withdrawal',
                target_id=withdrawal.id,
                target_description=f"Withdrawal: {withdrawal.amount}",
                description=f"Withdrawal approved: {withdrawal.amount}",
                reason=notes
            )
            
            logger.info(f"Withdrawal {withdrawal.id} approved by {admin.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve withdrawal {withdrawal.id}: {e}")
            return False
    
    def reject_withdrawal(self, withdrawal: Withdrawal, admin: User, reason: str) -> bool:
        """Reject a withdrawal"""
        try:
            withdrawal.status = 'rejected'
            withdrawal.processed_by = admin
            withdrawal.processed_at = timezone.now()
            withdrawal.admin_notes = reason
            withdrawal.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='withdrawal_reject',
                target_type='Withdrawal',
                target_id=withdrawal.id,
                target_description=f"Withdrawal: {withdrawal.amount}",
                description=f"Withdrawal rejected: {withdrawal.amount}",
                reason=reason
            )
            
            logger.info(f"Withdrawal {withdrawal.id} rejected by {admin.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject withdrawal {withdrawal.id}: {e}")
            return False


class SystemConfigurationService:
    """Service for system configuration management"""
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current system configuration"""
        try:
            configs = SystemConfiguration.objects.filter(is_active=True)
            configuration = {}
            
            for config in configs:
                configuration[config.key] = {
                    'value': config.value,
                    'description': config.description,
                    'data_type': config.data_type
                }
            
            return configuration
            
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            return {}
    
    def update_configuration(self, key: str, value: Any, admin: User, reason: str = '') -> bool:
        """Update system configuration"""
        try:
            config, created = SystemConfiguration.objects.get_or_create(
                key=key,
                defaults={
                    'value': str(value),
                    'description': f'Configuration for {key}',
                    'data_type': type(value).__name__,
                    'is_active': True
                }
            )
            
            if not created:
                config.value = str(value)
                config.updated_at = timezone.now()
                config.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin=admin,
                action_type='system_config',
                target_type='SystemConfiguration',
                target_id=config.id,
                target_description=f"Config: {key}",
                description=f"Configuration updated: {key} = {value}",
                reason=reason
            )
            
            logger.info(f"Configuration {key} updated by {admin.username}: {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration {key}: {e}")
            return False
