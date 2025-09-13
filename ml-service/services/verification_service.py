import numpy as np
import cv2
import pytesseract
from PIL import Image
import requests
import asyncio
import aiohttp
import io
from typing import Dict, Any, List
import re
import hashlib
import time

from models.schemas import VerificationRequest, VerificationResponse, VerificationStatus

class VerificationService:
    def __init__(self):
        self.models_loaded = False
        self.token_patterns = {
            'instagram': r'#[A-Za-z0-9_]+',
            'twitter': r'#[A-Za-z0-9_]+',
            'facebook': r'#[A-Za-z0-9_]+',
            'tiktok': r'#[A-Za-z0-9_]+',
            'youtube': r'#[A-Za-z0-9_]+',
        }
        
    async def load_models(self):
        """Load verification models"""
        # In a real implementation, this would load pre-trained models
        # For now, we'll just mark as loaded
        self.models_loaded = True
        print("Verification models loaded")
    
    async def verify_attempt(self, request: VerificationRequest) -> VerificationResponse:
        """Verify a job attempt using multiple methods"""
        verification_methods = []
        fraud_indicators = []
        evidence = {}
        confidence_scores = []
        
        # 1. Screenshot Analysis
        if request.screenshot_url:
            screenshot_result = await self._analyze_screenshot(request.screenshot_url)
            verification_methods.append("screenshot_analysis")
            confidence_scores.append(screenshot_result['confidence'])
            evidence['screenshot'] = screenshot_result
            if screenshot_result['fraud_indicators']:
                fraud_indicators.extend(screenshot_result['fraud_indicators'])
        
        # 2. Token Verification
        if request.token_data:
            token_result = await self._verify_token(request.token_data, request.platform)
            verification_methods.append("token_verification")
            confidence_scores.append(token_result['confidence'])
            evidence['token'] = token_result
            if token_result['fraud_indicators']:
                fraud_indicators.extend(token_result['fraud_indicators'])
        
        # 3. Behavioral Analysis
        behavior_result = await self._analyze_behavior(request)
        verification_methods.append("behavioral_analysis")
        confidence_scores.append(behavior_result['confidence'])
        evidence['behavior'] = behavior_result
        if behavior_result['fraud_indicators']:
            fraud_indicators.extend(behavior_result['fraud_indicators'])
        
        # 4. Content Analysis
        if 'content' in request.proof_data:
            content_result = await self._analyze_content(request.proof_data['content'])
            verification_methods.append("content_analysis")
            confidence_scores.append(content_result['confidence'])
            evidence['content'] = content_result
            if content_result['fraud_indicators']:
                fraud_indicators.extend(content_result['fraud_indicators'])
        
        # Calculate overall confidence and status
        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
        ai_score = overall_confidence
        
        # Determine verification status
        if overall_confidence >= 0.8:
            status = VerificationStatus.VERIFIED
        elif overall_confidence >= 0.6:
            status = VerificationStatus.MANUAL_REVIEW
        else:
            status = VerificationStatus.REJECTED
        
        # Check if manual review is required
        requires_manual_review = (
            len(fraud_indicators) > 0 or 
            overall_confidence < 0.8 or
            len(verification_methods) < 2
        )
        
        reasoning = self._generate_reasoning(verification_methods, confidence_scores, fraud_indicators)
        
        return VerificationResponse(
            job_id=request.job_id,
            status=status,
            confidence=overall_confidence,
            verification_methods=verification_methods,
            ai_score=ai_score,
            reasoning=reasoning,
            requires_manual_review=requires_manual_review,
            fraud_indicators=fraud_indicators if fraud_indicators else None,
            evidence=evidence
        )
    
    async def _analyze_screenshot(self, screenshot_url: str) -> Dict[str, Any]:
        """Analyze screenshot for authenticity"""
        try:
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(screenshot_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                    else:
                        return {
                            'confidence': 0.3,
                            'fraud_indicators': ['screenshot_download_failed'],
                            'analysis': 'Failed to download screenshot'
                        }
            
            # Load image
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Basic image analysis
            fraud_indicators = []
            confidence = 0.7  # Base confidence
            
            # Check image dimensions
            height, width = image_array.shape[:2]
            if height < 100 or width < 100:
                fraud_indicators.append('screenshot_too_small')
                confidence -= 0.2
            
            # Check for obvious manipulation (simplified)
            if self._detect_image_manipulation(image_array):
                fraud_indicators.append('image_manipulation_detected')
                confidence -= 0.3
            
            # OCR to extract text
            try:
                text = pytesseract.image_to_string(image)
                if len(text.strip()) < 10:
                    fraud_indicators.append('insufficient_text_content')
                    confidence -= 0.1
            except:
                fraud_indicators.append('ocr_failed')
                confidence -= 0.1
            
            return {
                'confidence': max(0.1, confidence),
                'fraud_indicators': fraud_indicators,
                'analysis': f'Image analysis completed. Dimensions: {width}x{height}',
                'text_extracted': len(text.strip()) if 'text' in locals() else 0
            }
            
        except Exception as e:
            return {
                'confidence': 0.2,
                'fraud_indicators': ['screenshot_analysis_failed'],
                'analysis': f'Screenshot analysis failed: {str(e)}'
            }
    
    def _detect_image_manipulation(self, image_array: np.ndarray) -> bool:
        """Simple image manipulation detection"""
        # This is a simplified version - in production, you'd use more sophisticated methods
        try:
            # Check for uniform regions that might indicate copy-paste
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Calculate local variance
            kernel = np.ones((3, 3), np.float32) / 9
            mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            sqr_mean = cv2.filter2D((gray.astype(np.float32))**2, -1, kernel)
            variance = sqr_mean - mean**2
            
            # If too many regions have very low variance, might be manipulated
            low_variance_ratio = np.sum(variance < 10) / variance.size
            return low_variance_ratio > 0.3
            
        except:
            return False
    
    async def _verify_token(self, token_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Verify token authenticity"""
        fraud_indicators = []
        confidence = 0.8  # Base confidence for token verification
        
        # Check token format
        if 'token' not in token_data:
            fraud_indicators.append('missing_token')
            confidence -= 0.5
        
        token = token_data.get('token', '')
        
        # Check token length and format
        if len(token) < 10:
            fraud_indicators.append('token_too_short')
            confidence -= 0.3
        
        # Check for platform-specific patterns
        if platform in self.token_patterns:
            pattern = self.token_patterns[platform]
            if not re.search(pattern, token):
                fraud_indicators.append('invalid_token_format')
                confidence -= 0.2
        
        # Check token timestamp (if provided)
        if 'timestamp' in token_data:
            token_time = token_data['timestamp']
            current_time = time.time()
            if current_time - token_time > 3600:  # Token older than 1 hour
                fraud_indicators.append('token_expired')
                confidence -= 0.2
        
        # Check token hash (if provided)
        if 'hash' in token_data:
            expected_hash = hashlib.sha256(token.encode()).hexdigest()
            if token_data['hash'] != expected_hash:
                fraud_indicators.append('token_hash_mismatch')
                confidence -= 0.4
        
        return {
            'confidence': max(0.1, confidence),
            'fraud_indicators': fraud_indicators,
            'analysis': f'Token verification completed for {platform}',
            'token_length': len(token),
            'has_timestamp': 'timestamp' in token_data,
            'has_hash': 'hash' in token_data
        }
    
    async def _analyze_behavior(self, request: VerificationRequest) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        fraud_indicators = []
        confidence = 0.6  # Base confidence for behavioral analysis
        
        # Check submission timing
        if 'submission_time' in request.metadata:
            submission_time = request.metadata['submission_time']
            # Check if submission is too fast (might be automated)
            if submission_time < 30:  # Less than 30 seconds
                fraud_indicators.append('submission_too_fast')
                confidence -= 0.2
        
        # Check for repetitive patterns
        if 'previous_attempts' in request.metadata:
            attempts = request.metadata['previous_attempts']
            if len(attempts) > 5:  # Too many attempts
                fraud_indicators.append('excessive_attempts')
                confidence -= 0.1
        
        # Check user agent and device info
        if 'user_agent' in request.metadata:
            user_agent = request.metadata['user_agent']
            if 'bot' in user_agent.lower() or 'automation' in user_agent.lower():
                fraud_indicators.append('suspicious_user_agent')
                confidence -= 0.3
        
        return {
            'confidence': max(0.1, confidence),
            'fraud_indicators': fraud_indicators,
            'analysis': 'Behavioral analysis completed',
            'submission_time': request.metadata.get('submission_time', 'unknown'),
            'attempt_count': len(request.metadata.get('previous_attempts', []))
        }
    
    async def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content quality and authenticity"""
        fraud_indicators = []
        confidence = 0.7  # Base confidence for content analysis
        
        # Check content length
        if len(content) < 10:
            fraud_indicators.append('content_too_short')
            confidence -= 0.3
        elif len(content) > 1000:
            fraud_indicators.append('content_too_long')
            confidence -= 0.1
        
        # Check for repetitive content
        words = content.lower().split()
        if len(words) > 0:
            unique_words = len(set(words))
            repetition_ratio = unique_words / len(words)
            if repetition_ratio < 0.5:
                fraud_indicators.append('high_content_repetition')
                confidence -= 0.2
        
        # Check for spam indicators
        spam_keywords = ['click here', 'buy now', 'free money', 'win prize']
        spam_count = sum(1 for keyword in spam_keywords if keyword in content.lower())
        if spam_count > 0:
            fraud_indicators.append('spam_keywords_detected')
            confidence -= 0.3
        
        # Check for gibberish
        if self._is_gibberish(content):
            fraud_indicators.append('gibberish_content')
            confidence -= 0.4
        
        return {
            'confidence': max(0.1, confidence),
            'fraud_indicators': fraud_indicators,
            'analysis': f'Content analysis completed. Length: {len(content)} chars',
            'word_count': len(words),
            'unique_word_ratio': repetition_ratio if len(words) > 0 else 0,
            'spam_keywords_found': spam_count
        }
    
    def _is_gibberish(self, text: str) -> bool:
        """Simple gibberish detection"""
        # Check for excessive special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            return True
        
        # Check for repeated characters
        if len(text) > 10:
            for i in range(len(text) - 4):
                if text[i:i+4] == text[i]*4:
                    return True
        
        return False
    
    def _generate_reasoning(self, methods: List[str], scores: List[float], fraud_indicators: List[str]) -> str:
        """Generate human-readable reasoning for verification result"""
        if not methods:
            return "No verification methods available"
        
        avg_score = np.mean(scores) if scores else 0
        method_count = len(methods)
        
        reasoning = f"Verification completed using {method_count} method(s): {', '.join(methods)}. "
        reasoning += f"Average confidence: {avg_score:.2f}. "
        
        if fraud_indicators:
            reasoning += f"Fraud indicators detected: {', '.join(fraud_indicators)}. "
        
        if avg_score >= 0.8:
            reasoning += "High confidence verification passed."
        elif avg_score >= 0.6:
            reasoning += "Medium confidence - manual review recommended."
        else:
            reasoning += "Low confidence - verification failed."
        
        return reasoning
