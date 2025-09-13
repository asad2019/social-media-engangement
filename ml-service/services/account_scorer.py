import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, Any
import asyncio

from models.schemas import AccountScoreRequest, AccountScoreResponse

class AccountScorer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'follower_count_log',
            'following_count_log', 
            'post_count_log',
            'account_age_days_log',
            'follower_following_ratio',
            'posts_per_day',
            'engagement_rate',
            'bio_length',
            'has_profile_pic',
            'account_completeness'
        ]
        self.model_path = "models/account_scorer.pkl"
        self.scaler_path = "models/account_scaler.pkl"
        
    async def load_model(self):
        """Load pre-trained model and scaler"""
        try:
            # Create models directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                print("Loaded pre-trained account scorer model")
            else:
                # Train a new model with synthetic data
                await self._train_model()
                print("Trained new account scorer model")
                
        except Exception as e:
            print(f"Error loading model: {e}")
            await self._train_model()
    
    async def _train_model(self):
        """Train a new model with synthetic data"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        # Generate realistic synthetic data
        follower_counts = np.random.lognormal(mean=8, sigma=2, size=n_samples)
        following_counts = np.random.lognormal(mean=6, sigma=1.5, size=n_samples)
        post_counts = np.random.lognormal(mean=4, sigma=1.5, size=n_samples)
        account_ages = np.random.exponential(scale=365, size=n_samples)
        
        # Calculate derived features
        follower_following_ratios = follower_counts / (following_counts + 1)
        posts_per_day = post_counts / (account_ages + 1)
        engagement_rates = np.random.beta(2, 8, size=n_samples)  # Most accounts have low engagement
        bio_lengths = np.random.poisson(50, size=n_samples)
        has_profile_pic = np.random.choice([0, 1], size=n_samples, p=[0.1, 0.9])
        
        # Account completeness score
        account_completeness = (
            (follower_counts > 100).astype(int) * 0.3 +
            (bio_lengths > 10).astype(int) * 0.3 +
            has_profile_pic * 0.2 +
            (post_counts > 10).astype(int) * 0.2
        )
        
        # Create features
        X = np.column_stack([
            np.log1p(follower_counts),
            np.log1p(following_counts),
            np.log1p(post_counts),
            np.log1p(account_ages),
            follower_following_ratios,
            posts_per_day,
            engagement_rates,
            bio_lengths,
            has_profile_pic,
            account_completeness
        ])
        
        # Generate labels (0 = low quality, 1 = high quality)
        # Higher quality accounts have more followers, better ratios, more engagement
        quality_scores = (
            np.log1p(follower_counts) * 0.3 +
            follower_following_ratios * 0.2 +
            engagement_rates * 0.3 +
            account_completeness * 0.2
        )
        
        # Normalize quality scores to 0-1
        quality_scores = (quality_scores - quality_scores.min()) / (quality_scores.max() - quality_scores.min())
        y = (quality_scores > 0.5).astype(int)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_scaled, y)
        
        # Save model and scaler
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
    
    def _extract_features(self, request: AccountScoreRequest) -> np.ndarray:
        """Extract features from account data"""
        # Calculate derived features
        follower_following_ratio = request.follower_count / (request.following_count + 1)
        posts_per_day = request.post_count / (request.account_age_days + 1)
        
        # Estimate engagement rate (placeholder - would need real data)
        engagement_rate = min(0.1, request.follower_count / 10000) if request.follower_count > 0 else 0
        
        # Bio features
        bio_length = len(request.bio_text) if request.bio_text else 0
        has_profile_pic = 1 if request.profile_picture_url else 0
        
        # Account completeness score
        account_completeness = (
            (request.follower_count > 100) * 0.3 +
            (bio_length > 10) * 0.3 +
            has_profile_pic * 0.2 +
            (request.post_count > 10) * 0.2
        )
        
        # Create feature vector
        features = np.array([
            np.log1p(request.follower_count),
            np.log1p(request.following_count),
            np.log1p(request.post_count),
            np.log1p(request.account_age_days),
            follower_following_ratio,
            posts_per_day,
            engagement_rate,
            bio_length,
            has_profile_pic,
            account_completeness
        ])
        
        return features.reshape(1, -1)
    
    async def score_account(self, request: AccountScoreRequest) -> float:
        """Score an account for quality"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Extract features
        features = self._extract_features(request)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Get prediction probability
        quality_prob = self.model.predict_proba(features_scaled)[0][1]
        
        # Convert to 0-1 score
        score = float(quality_prob)
        
        return score
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the model"""
        if self.model is None:
            return {}
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def analyze_account(self, request: AccountScoreRequest) -> Dict[str, Any]:
        """Provide detailed account analysis"""
        features = self._extract_features(request)
        
        analysis = {
            "follower_count": request.follower_count,
            "following_count": request.following_count,
            "post_count": request.post_count,
            "account_age_days": request.account_age_days,
            "follower_following_ratio": request.follower_count / (request.following_count + 1),
            "posts_per_day": request.post_count / (request.account_age_days + 1),
            "bio_length": len(request.bio_text) if request.bio_text else 0,
            "has_profile_pic": bool(request.profile_picture_url),
            "account_completeness": (
                (request.follower_count > 100) * 0.3 +
                (len(request.bio_text or "") > 10) * 0.3 +
                bool(request.profile_picture_url) * 0.2 +
                (request.post_count > 10) * 0.2
            )
        }
        
        return analysis
