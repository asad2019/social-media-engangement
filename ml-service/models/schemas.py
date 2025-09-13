from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class PlatformType(str, Enum):
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"

class AccountScoreRequest(BaseModel):
    account_id: str
    platform: PlatformType
    username: str
    follower_count: int
    following_count: int
    post_count: int
    account_age_days: int
    bio_text: Optional[str] = None
    profile_picture_url: Optional[str] = None
    recent_posts: Optional[List[Dict[str, Any]]] = None
    engagement_metrics: Optional[Dict[str, float]] = None

class AccountScoreResponse(BaseModel):
    account_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    features_used: List[str]
    reasoning: str
    risk_factors: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class VerificationRequest(BaseModel):
    job_id: str
    user_id: str
    platform: PlatformType
    task_type: str
    proof_data: Dict[str, Any]
    screenshot_url: Optional[str] = None
    token_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class VerificationResponse(BaseModel):
    job_id: str
    status: VerificationStatus
    confidence: float = Field(..., ge=0.0, le=1.0)
    verification_methods: List[str]
    ai_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    requires_manual_review: bool = False
    fraud_indicators: Optional[List[str]] = None
    evidence: Optional[Dict[str, Any]] = None

class CommentAnalysisRequest(BaseModel):
    comment_id: str
    text: str
    platform: PlatformType
    user_id: str
    post_context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class CommentAnalysisResponse(BaseModel):
    comment_id: str
    quality_score: float = Field(..., ge=0.0, le=1.0)
    authenticity_score: float = Field(..., ge=0.0, le=1.0)
    sentiment: str
    complexity_score: float = Field(..., ge=0.0, le=1.0)
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    spam_probability: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    flags: Optional[List[str]] = None

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, bool]
    timestamp: Optional[str] = None

class ModelInfo(BaseModel):
    model_type: str
    version: str
    features: List[str]
    accuracy: Optional[float] = None
    last_trained: Optional[str] = None

class BatchVerificationRequest(BaseModel):
    verifications: List[VerificationRequest]
    batch_id: str

class BatchVerificationResponse(BaseModel):
    batch_id: str
    results: List[VerificationResponse]
    processing_time: float
    success_count: int
    failure_count: int
