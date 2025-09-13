from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from services.account_scorer import AccountScorer
from services.verification_service import VerificationService
from services.comment_analyzer import CommentAnalyzer
from models.schemas import (
    AccountScoreRequest,
    AccountScoreResponse,
    VerificationRequest,
    VerificationResponse,
    CommentAnalysisRequest,
    CommentAnalysisResponse,
    HealthResponse,
)

# Load environment variables
load_dotenv()

# Global services
account_scorer = None
verification_service = None
comment_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global account_scorer, verification_service, comment_analyzer
    
    print("Initializing ML services...")
    
    # Initialize services
    account_scorer = AccountScorer()
    verification_service = VerificationService()
    comment_analyzer = CommentAnalyzer()
    
    # Load models
    await account_scorer.load_model()
    await verification_service.load_models()
    await comment_analyzer.load_model()
    
    print("ML services initialized successfully!")
    
    yield
    
    # Cleanup on shutdown
    print("Shutting down ML services...")

# Create FastAPI app
app = FastAPI(
    title="Engagement Platform ML Service",
    description="Machine Learning service for account scoring and verification",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        services={
            "account_scorer": account_scorer is not None,
            "verification_service": verification_service is not None,
            "comment_analyzer": comment_analyzer is not None,
        }
    )

@app.post("/score-account", response_model=AccountScoreResponse)
async def score_account(request: AccountScoreRequest):
    """Score a social media account for quality"""
    if not account_scorer:
        raise HTTPException(status_code=503, detail="Account scorer not initialized")
    
    try:
        score = await account_scorer.score_account(request)
        return AccountScoreResponse(
            account_id=request.account_id,
            score=score,
            confidence=0.85,  # Placeholder
            features_used=["follower_count", "account_age", "activity_level"],
            reasoning="Account scored based on follower count, age, and activity patterns"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@app.post("/verify-attempt", response_model=VerificationResponse)
async def verify_attempt(request: VerificationRequest):
    """Verify a job attempt using multiple methods"""
    if not verification_service:
        raise HTTPException(status_code=503, detail="Verification service not initialized")
    
    try:
        result = await verification_service.verify_attempt(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.post("/analyze-comment", response_model=CommentAnalysisResponse)
async def analyze_comment(request: CommentAnalysisRequest):
    """Analyze comment quality and authenticity"""
    if not comment_analyzer:
        raise HTTPException(status_code=503, detail="Comment analyzer not initialized")
    
    try:
        analysis = await comment_analyzer.analyze_comment(request)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comment analysis failed: {str(e)}")

@app.get("/models/info")
async def get_models_info():
    """Get information about loaded models"""
    return {
        "account_scorer": {
            "model_type": "Random Forest",
            "version": "1.0.0",
            "features": ["follower_count", "account_age", "activity_level", "engagement_ratio"]
        },
        "verification_service": {
            "models": ["screenshot_analyzer", "token_verifier", "behavior_analyzer"],
            "version": "1.0.0"
        },
        "comment_analyzer": {
            "model_type": "Logistic Regression",
            "version": "1.0.0",
            "features": ["length", "uniqueness", "sentiment", "complexity"]
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
