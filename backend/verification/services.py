import asyncio
import httpx
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json
import hashlib
import time

from .models import (
    VerificationRule, VerificationSession, VerificationLog,
    ManualReviewQueue, FraudDetection, FraudAlert
)
from jobs.models import Job, JobAttempt
from users.models import User

logger = logging.getLogger(__name__)


class VerificationService:
    """Main verification service that orchestrates the verification pipeline"""
    
    def __init__(self):
        self.ml_service_url = settings.ML_SERVICE_URL
        self.tracker_service_url = settings.TRACKER_SERVICE_URL
    
    async def verify_job_attempt(self, job_attempt: JobAttempt) -> Dict[str, Any]:
        """Main verification method for job attempts"""
        try:
            # Get verification rule for this job
            verification_rule = await self._get_verification_rule(
                job_attempt.job.campaign.platform,
                job_attempt.job.campaign.engagement_type
            )
            
            if not verification_rule:
                return {
                    'status': 'failed',
                    'reason': 'No verification rule found',
                    'confidence': 0.0
                }
            
            # Create verification session
            session = VerificationSession.objects.create(
                job_attempt=job_attempt,
                verification_rule=verification_rule,
                status='pending',
                started_at=timezone.now()
            )
            
            # Run verification pipeline
            result = await self._run_verification_pipeline(session, verification_rule)
            
            # Update session
            session.status = result['status']
            session.completed_at = timezone.now()
            session.ai_score = result.get('ai_score', 0.0)
            session.confidence = result.get('confidence', 0.0)
            session.reasoning = result.get('reasoning', '')
            session.evidence = result.get('evidence', {})
            session.save()
            
            # Update job attempt
            job_attempt.verification_status = result['status']
            job_attempt.ai_score = result.get('ai_score', 0.0)
            job_attempt.save()
            
            # Handle fraud detection
            if result.get('fraud_indicators'):
                await self._handle_fraud_detection(job_attempt, result['fraud_indicators'])
            
            # Add to manual review if needed
            if result['status'] == 'manual_review':
                await self._add_to_manual_review(job_attempt, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Verification failed for job attempt {job_attempt.id}: {e}")
            return {
                'status': 'failed',
                'reason': str(e),
                'confidence': 0.0
            }
    
    async def _get_verification_rule(self, platform: str, engagement_type: str) -> Optional[VerificationRule]:
        """Get verification rule for platform and engagement type"""
        try:
            return VerificationRule.objects.get(
                platform=platform,
                engagement_type=engagement_type,
                is_active=True
            )
        except VerificationRule.DoesNotExist:
            return None
    
    async def _run_verification_pipeline(self, session: VerificationSession, rule: VerificationRule) -> Dict[str, Any]:
        """Run the verification pipeline using configured methods"""
        verification_methods = rule.verification_methods
        results = []
        overall_confidence = 0.0
        fraud_indicators = []
        evidence = {}
        
        for method in verification_methods:
            try:
                if method == 'deterministic':
                    result = await self._deterministic_check(session)
                elif method == 'tokenized':
                    result = await self._tokenized_verification(session)
                elif method == 'screenshot':
                    result = await self._screenshot_analysis(session)
                elif method == 'headless':
                    result = await self._headless_browser_check(session)
                elif method == 'ml':
                    result = await self._ml_verification(session)
                else:
                    logger.warning(f"Unknown verification method: {method}")
                    continue
                
                results.append(result)
                overall_confidence += result.get('confidence', 0.0)
                
                if result.get('fraud_indicators'):
                    fraud_indicators.extend(result['fraud_indicators'])
                
                if result.get('evidence'):
                    evidence[method] = result['evidence']
                
                # If we have high confidence, we can stop early
                if result.get('confidence', 0.0) >= rule.pass_threshold:
                    break
                    
            except Exception as e:
                logger.error(f"Verification method {method} failed: {e}")
                continue
        
        # Calculate overall result
        if results:
            overall_confidence = overall_confidence / len(results)
        
        # Determine final status
        if overall_confidence >= rule.pass_threshold:
            status = 'verified'
        elif overall_confidence >= rule.manual_review_threshold:
            status = 'manual_review'
        else:
            status = 'rejected'
        
        return {
            'status': status,
            'confidence': overall_confidence,
            'ai_score': overall_confidence,
            'verification_methods': verification_methods,
            'fraud_indicators': fraud_indicators,
            'evidence': evidence,
            'reasoning': self._generate_reasoning(results, overall_confidence, fraud_indicators)
        }
    
    async def _deterministic_check(self, session: VerificationSession) -> Dict[str, Any]:
        """Perform deterministic verification checks"""
        job_attempt = session.job_attempt
        job = job_attempt.job
        campaign = job.campaign
        
        fraud_indicators = []
        confidence = 0.8  # Base confidence for deterministic checks
        
        # Check proof data structure
        if not job_attempt.proof_data:
            fraud_indicators.append('missing_proof_data')
            confidence -= 0.5
        
        # Check timestamp validity
        if 'timestamp' in job_attempt.proof_data:
            timestamp = job_attempt.proof_data['timestamp']
            current_time = time.time()
            if current_time - timestamp > 3600:  # More than 1 hour old
                fraud_indicators.append('proof_timestamp_too_old')
                confidence -= 0.2
        
        # Check URL validity for website visits
        if campaign.engagement_type == 'visit' and 'url' in job_attempt.proof_data:
            url = job_attempt.proof_data['url']
            if not url.startswith(('http://', 'https://')):
                fraud_indicators.append('invalid_url_format')
                confidence -= 0.3
        
        # Check social media post ID format
        if campaign.platform in ['instagram', 'twitter', 'facebook']:
            if 'post_id' in job_attempt.proof_data:
                post_id = job_attempt.proof_data['post_id']
                if len(post_id) < 10:  # Most social media IDs are longer
                    fraud_indicators.append('suspicious_post_id')
                    confidence -= 0.2
        
        return {
            'method': 'deterministic',
            'confidence': max(0.0, confidence),
            'fraud_indicators': fraud_indicators,
            'evidence': {
                'proof_data_present': bool(job_attempt.proof_data),
                'timestamp_valid': 'timestamp' in job_attempt.proof_data,
                'data_structure_valid': len(job_attempt.proof_data or {}) > 0
            }
        }
    
    async def _tokenized_verification(self, session: VerificationSession) -> Dict[str, Any]:
        """Perform tokenized verification"""
        job_attempt = session.job_attempt
        job = job_attempt.job
        campaign = job.campaign
        
        fraud_indicators = []
        confidence = 0.7  # Base confidence for tokenized verification
        
        # Check if token is present
        if 'token' not in job_attempt.proof_data:
            fraud_indicators.append('missing_verification_token')
            confidence -= 0.5
            return {
                'method': 'tokenized',
                'confidence': max(0.0, confidence),
                'fraud_indicators': fraud_indicators,
                'evidence': {'token_present': False}
            }
        
        token = job_attempt.proof_data['token']
        
        # Validate token format
        if len(token) < 20:  # Tokens should be reasonably long
            fraud_indicators.append('token_too_short')
            confidence -= 0.3
        
        # Check token hash if provided
        if 'token_hash' in job_attempt.proof_data:
            expected_hash = hashlib.sha256(token.encode()).hexdigest()
            provided_hash = job_attempt.proof_data['token_hash']
            if expected_hash != provided_hash:
                fraud_indicators.append('token_hash_mismatch')
                confidence -= 0.4
        
        # Check token timestamp
        if 'token_timestamp' in job_attempt.proof_data:
            token_time = job_attempt.proof_data['token_timestamp']
            current_time = time.time()
            if current_time - token_time > 300:  # Token older than 5 minutes
                fraud_indicators.append('token_expired')
                confidence -= 0.2
        
        return {
            'method': 'tokenized',
            'confidence': max(0.0, confidence),
            'fraud_indicators': fraud_indicators,
            'evidence': {
                'token_present': True,
                'token_length': len(token),
                'has_hash': 'token_hash' in job_attempt.proof_data,
                'has_timestamp': 'token_timestamp' in job_attempt.proof_data
            }
        }
    
    async def _screenshot_analysis(self, session: VerificationSession) -> Dict[str, Any]:
        """Perform screenshot analysis using ML service"""
        job_attempt = session.job_attempt
        
        if 'screenshot_url' not in job_attempt.proof_data:
            return {
                'method': 'screenshot',
                'confidence': 0.0,
                'fraud_indicators': ['no_screenshot_provided'],
                'evidence': {'screenshot_present': False}
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ml_service_url}/verify-attempt",
                    json={
                        'job_id': str(job_attempt.job.id),
                        'user_id': str(job_attempt.earner.id),
                        'platform': job_attempt.job.campaign.platform,
                        'task_type': job_attempt.job.campaign.engagement_type,
                        'proof_data': job_attempt.proof_data,
                        'screenshot_url': job_attempt.proof_data.get('screenshot_url'),
                        'metadata': {
                            'submission_time': time.time() - job_attempt.created_at.timestamp(),
                            'user_agent': job_attempt.proof_data.get('user_agent', ''),
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    ml_result = response.json()
                    return {
                        'method': 'screenshot',
                        'confidence': ml_result.get('confidence', 0.0),
                        'fraud_indicators': ml_result.get('fraud_indicators', []),
                        'evidence': ml_result.get('evidence', {})
                    }
                else:
                    logger.error(f"ML service returned status {response.status_code}")
                    return {
                        'method': 'screenshot',
                        'confidence': 0.0,
                        'fraud_indicators': ['ml_service_error'],
                        'evidence': {'ml_service_status': response.status_code}
                    }
                    
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return {
                'method': 'screenshot',
                'confidence': 0.0,
                'fraud_indicators': ['screenshot_analysis_failed'],
                'evidence': {'error': str(e)}
            }
    
    async def _headless_browser_check(self, session: VerificationSession) -> Dict[str, Any]:
        """Perform headless browser verification"""
        job_attempt = session.job_attempt
        job = job_attempt.job
        campaign = job.campaign
        
        # This would integrate with a headless browser service
        # For now, return a placeholder implementation
        
        fraud_indicators = []
        confidence = 0.6  # Base confidence for headless browser checks
        
        # Check if we have the necessary data for headless verification
        required_fields = ['url', 'post_id', 'account_username']
        missing_fields = [field for field in required_fields if field not in job_attempt.proof_data]
        
        if missing_fields:
            fraud_indicators.append(f'missing_fields: {", ".join(missing_fields)}')
            confidence -= 0.3
        
        return {
            'method': 'headless',
            'confidence': max(0.0, confidence),
            'fraud_indicators': fraud_indicators,
            'evidence': {
                'required_fields_present': len(missing_fields) == 0,
                'missing_fields': missing_fields
            }
        }
    
    async def _ml_verification(self, session: VerificationSession) -> Dict[str, Any]:
        """Perform ML-based verification"""
        job_attempt = session.job_attempt
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ml_service_url}/verify-attempt",
                    json={
                        'job_id': str(job_attempt.job.id),
                        'user_id': str(job_attempt.earner.id),
                        'platform': job_attempt.job.campaign.platform,
                        'task_type': job_attempt.job.campaign.engagement_type,
                        'proof_data': job_attempt.proof_data,
                        'metadata': {
                            'submission_time': time.time() - job_attempt.created_at.timestamp(),
                            'user_reputation': float(job_attempt.earner.reputation_score),
                            'account_age_days': (timezone.now() - job_attempt.earner.date_joined).days,
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    ml_result = response.json()
                    return {
                        'method': 'ml',
                        'confidence': ml_result.get('confidence', 0.0),
                        'fraud_indicators': ml_result.get('fraud_indicators', []),
                        'evidence': ml_result.get('evidence', {})
                    }
                else:
                    logger.error(f"ML service returned status {response.status_code}")
                    return {
                        'method': 'ml',
                        'confidence': 0.0,
                        'fraud_indicators': ['ml_service_error'],
                        'evidence': {'ml_service_status': response.status_code}
                    }
                    
        except Exception as e:
            logger.error(f"ML verification failed: {e}")
            return {
                'method': 'ml',
                'confidence': 0.0,
                'fraud_indicators': ['ml_verification_failed'],
                'evidence': {'error': str(e)}
            }
    
    async def _handle_fraud_detection(self, job_attempt: JobAttempt, fraud_indicators: List[str]):
        """Handle fraud detection results"""
        try:
            # Create fraud detection record
            fraud_detection = FraudDetection.objects.create(
                job_attempt=job_attempt,
                fraud_score=0.8,  # Calculate based on indicators
                fraud_indicators=fraud_indicators,
                status='detected',
                detected_at=timezone.now()
            )
            
            # Create fraud alert if score is high
            if len(fraud_indicators) >= 3:  # Threshold for alert
                FraudAlert.objects.create(
                    fraud_detection=fraud_detection,
                    severity='high',
                    status='active',
                    description=f"Multiple fraud indicators detected: {', '.join(fraud_indicators)}"
                )
            
            logger.info(f"Fraud detected for job attempt {job_attempt.id}: {fraud_indicators}")
            
        except Exception as e:
            logger.error(f"Failed to handle fraud detection: {e}")
    
    async def _add_to_manual_review(self, job_attempt: JobAttempt, result: Dict[str, Any]):
        """Add job attempt to manual review queue"""
        try:
            ManualReviewQueue.objects.create(
                job_attempt=job_attempt,
                priority='medium',
                reason='verification_uncertainty',
                evidence=result.get('evidence', {}),
                fraud_indicators=result.get('fraud_indicators', []),
                status='pending',
                created_at=timezone.now()
            )
            
            logger.info(f"Added job attempt {job_attempt.id} to manual review queue")
            
        except Exception as e:
            logger.error(f"Failed to add to manual review: {e}")
    
    def _generate_reasoning(self, results: List[Dict], overall_confidence: float, fraud_indicators: List[str]) -> str:
        """Generate human-readable reasoning for verification result"""
        if not results:
            return "No verification methods were successful"
        
        method_count = len(results)
        reasoning = f"Verification completed using {method_count} method(s). "
        reasoning += f"Overall confidence: {overall_confidence:.2f}. "
        
        if fraud_indicators:
            reasoning += f"Fraud indicators detected: {', '.join(fraud_indicators)}. "
        
        if overall_confidence >= 0.8:
            reasoning += "High confidence verification passed."
        elif overall_confidence >= 0.6:
            reasoning += "Medium confidence - manual review recommended."
        else:
            reasoning += "Low confidence - verification failed."
        
        return reasoning


class ManualReviewService:
    """Service for handling manual review queue"""
    
    def get_pending_reviews(self, limit: int = 50) -> List[ManualReviewQueue]:
        """Get pending manual reviews"""
        return ManualReviewQueue.objects.filter(
            status='pending'
        ).order_by('-priority', 'created_at')[:limit]
    
    def approve_review(self, review_id: str, reviewer: User, notes: str = '') -> bool:
        """Approve a manual review"""
        try:
            review = ManualReviewQueue.objects.get(id=review_id, status='pending')
            
            # Update review
            review.status = 'approved'
            review.reviewed_by = reviewer
            review.reviewed_at = timezone.now()
            review.reviewer_notes = notes
            review.save()
            
            # Update job attempt
            job_attempt = review.job_attempt
            job_attempt.verification_status = 'verified'
            job_attempt.save()
            
            # Process payment
            self._process_approved_job(job_attempt)
            
            return True
            
        except ManualReviewQueue.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to approve review {review_id}: {e}")
            return False
    
    def reject_review(self, review_id: str, reviewer: User, reason: str = '') -> bool:
        """Reject a manual review"""
        try:
            review = ManualReviewQueue.objects.get(id=review_id, status='pending')
            
            # Update review
            review.status = 'rejected'
            review.reviewed_by = reviewer
            review.reviewed_at = timezone.now()
            review.reviewer_notes = reason
            review.save()
            
            # Update job attempt
            job_attempt = review.job_attempt
            job_attempt.verification_status = 'rejected'
            job_attempt.save()
            
            return True
            
        except ManualReviewQueue.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to reject review {review_id}: {e}")
            return False
    
    def _process_approved_job(self, job_attempt: JobAttempt):
        """Process payment for approved job"""
        try:
            from wallets.models import WalletTransaction
            
            # Create credit transaction for earner
            WalletTransaction.create_transaction(
                user=job_attempt.earner,
                transaction_type='credit',
                amount=job_attempt.reward_amount,
                reference=f"job_completion_{job_attempt.job.id}",
                description=f"Payment for completing job {job_attempt.job.id}",
                metadata={
                    'job_id': str(job_attempt.job.id),
                    'job_attempt_id': str(job_attempt.id),
                    'campaign_id': str(job_attempt.job.campaign.id),
                }
            )
            
            logger.info(f"Processed payment for job attempt {job_attempt.id}")
            
        except Exception as e:
            logger.error(f"Failed to process payment for job attempt {job_attempt.id}: {e}")


class FraudDetectionService:
    """Service for fraud detection and prevention"""
    
    def analyze_user_patterns(self, user: User) -> Dict[str, Any]:
        """Analyze user patterns for fraud detection"""
        try:
            # Get user's recent job attempts
            recent_attempts = JobAttempt.objects.filter(
                earner=user,
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).order_by('-created_at')[:100]
            
            if not recent_attempts:
                return {'fraud_score': 0.0, 'indicators': []}
            
            fraud_indicators = []
            fraud_score = 0.0
            
            # Check submission patterns
            submission_times = [attempt.created_at for attempt in recent_attempts]
            if len(submission_times) > 1:
                time_diffs = [(submission_times[i] - submission_times[i+1]).total_seconds() 
                             for i in range(len(submission_times)-1)]
                avg_time_diff = sum(time_diffs) / len(time_diffs)
                
                if avg_time_diff < 60:  # Less than 1 minute between submissions
                    fraud_indicators.append('rapid_submissions')
                    fraud_score += 0.3
            
            # Check success rate
            successful_attempts = recent_attempts.filter(verification_status='verified').count()
            success_rate = successful_attempts / len(recent_attempts)
            
            if success_rate > 0.95:  # Suspiciously high success rate
                fraud_indicators.append('suspiciously_high_success_rate')
                fraud_score += 0.2
            
            # Check platform diversity
            platforms = set(attempt.job.campaign.platform for attempt in recent_attempts)
            if len(platforms) == 1 and len(recent_attempts) > 10:
                fraud_indicators.append('single_platform_focus')
                fraud_score += 0.1
            
            return {
                'fraud_score': min(1.0, fraud_score),
                'indicators': fraud_indicators,
                'total_attempts': len(recent_attempts),
                'success_rate': success_rate,
                'platforms_used': len(platforms)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user patterns for {user.id}: {e}")
            return {'fraud_score': 0.0, 'indicators': ['analysis_failed']}
    
    def create_fraud_alert(self, user: User, reason: str, severity: str = 'medium') -> FraudAlert:
        """Create a fraud alert for a user"""
        try:
            fraud_detection = FraudDetection.objects.create(
                job_attempt=None,  # System-wide detection
                fraud_score=0.8,
                fraud_indicators=[reason],
                status='detected',
                detected_at=timezone.now()
            )
            
            alert = FraudAlert.objects.create(
                fraud_detection=fraud_detection,
                user=user,
                severity=severity,
                status='active',
                description=reason
            )
            
            logger.info(f"Created fraud alert for user {user.id}: {reason}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create fraud alert: {e}")
            raise
