import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import re
import string
from typing import Dict, Any, List
import asyncio
import os

from models.schemas import CommentAnalysisRequest, CommentAnalysisResponse

class CommentAnalyzer:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'length',
            'word_count',
            'avg_word_length',
            'special_char_ratio',
            'uppercase_ratio',
            'digit_ratio',
            'punctuation_ratio',
            'unique_word_ratio',
            'sentiment_score',
            'complexity_score'
        ]
        self.model_path = "models/comment_analyzer.pkl"
        self.vectorizer_path = "models/comment_vectorizer.pkl"
        self.scaler_path = "models/comment_scaler.pkl"
        
    async def load_model(self):
        """Load pre-trained model and vectorizer"""
        try:
            # Create models directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            
            if (os.path.exists(self.model_path) and 
                os.path.exists(self.vectorizer_path) and 
                os.path.exists(self.scaler_path)):
                
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.scaler = joblib.load(self.scaler_path)
                print("Loaded pre-trained comment analyzer model")
            else:
                # Train a new model with synthetic data
                await self._train_model()
                print("Trained new comment analyzer model")
                
        except Exception as e:
            print(f"Error loading model: {e}")
            await self._train_model()
    
    async def _train_model(self):
        """Train a new model with synthetic data"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 2000
        
        # Generate realistic comment data
        comments = []
        labels = []
        
        # High quality comments
        for _ in range(n_samples // 2):
            comment = self._generate_high_quality_comment()
            comments.append(comment)
            labels.append(1)  # High quality
        
        # Low quality/spam comments
        for _ in range(n_samples // 2):
            comment = self._generate_low_quality_comment()
            comments.append(comment)
            labels.append(0)  # Low quality
        
        # Extract features
        X_features = []
        for comment in comments:
            features = self._extract_text_features(comment)
            X_features.append(features)
        
        X_features = np.array(X_features)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_features)
        
        # Train model
        self.model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'
        )
        self.model.fit(X_scaled, labels)
        
        # Train TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.vectorizer.fit(comments)
        
        # Save models
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        joblib.dump(self.scaler, self.scaler_path)
    
    def _generate_high_quality_comment(self) -> str:
        """Generate a high quality comment"""
        templates = [
            "This is really helpful, thank you for sharing!",
            "I love this idea, it's so creative and well thought out.",
            "Great post! This really resonates with me.",
            "Thanks for the detailed explanation, it makes so much sense now.",
            "This is exactly what I was looking for, perfect timing!",
            "Amazing work! The quality is outstanding.",
            "I appreciate you taking the time to share this valuable information.",
            "This is brilliant! I never thought of it this way before.",
            "Excellent point! You've given me a new perspective.",
            "This is so well written and informative, thank you!"
        ]
        return np.random.choice(templates)
    
    def _generate_low_quality_comment(self) -> str:
        """Generate a low quality/spam comment"""
        templates = [
            "click here now!!!",
            "buy buy buy $$$",
            "free money click link",
            "asdfghjkl",
            "!!!!!!!!!!",
            "spam spam spam",
            "click here for free stuff",
            "win win win prize",
            "buy now limited time",
            "free free free money"
        ]
        return np.random.choice(templates)
    
    def _extract_text_features(self, text: str) -> List[float]:
        """Extract features from text"""
        # Basic length features
        length = len(text)
        words = text.split()
        word_count = len(words)
        avg_word_length = np.mean([len(word) for word in words]) if words else 0
        
        # Character ratios
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_char_ratio = special_chars / length if length > 0 else 0
        
        uppercase_chars = sum(1 for c in text if c.isupper())
        uppercase_ratio = uppercase_chars / length if length > 0 else 0
        
        digit_chars = sum(1 for c in text if c.isdigit())
        digit_ratio = digit_chars / length if length > 0 else 0
        
        punctuation_chars = sum(1 for c in text if c in string.punctuation)
        punctuation_ratio = punctuation_chars / length if length > 0 else 0
        
        # Uniqueness
        unique_words = len(set(word.lower() for word in words))
        unique_word_ratio = unique_words / word_count if word_count > 0 else 0
        
        # Sentiment (simplified)
        positive_words = ['good', 'great', 'awesome', 'amazing', 'love', 'like', 'excellent', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'horrible', 'worst']
        
        positive_count = sum(1 for word in words if word.lower() in positive_words)
        negative_count = sum(1 for word in words if word.lower() in negative_words)
        sentiment_score = (positive_count - negative_count) / word_count if word_count > 0 else 0
        
        # Complexity (average word length + sentence structure)
        complexity_score = avg_word_length + (unique_word_ratio * 10)
        
        return [
            length,
            word_count,
            avg_word_length,
            special_char_ratio,
            uppercase_ratio,
            digit_ratio,
            punctuation_ratio,
            unique_word_ratio,
            sentiment_score,
            complexity_score
        ]
    
    async def analyze_comment(self, request: CommentAnalysisRequest) -> CommentAnalysisResponse:
        """Analyze comment quality and authenticity"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("Model not loaded")
        
        text = request.text
        
        # Extract features
        features = self._extract_text_features(text)
        features_array = np.array(features).reshape(1, -1)
        
        # Scale features
        features_scaled = self.scaler.transform(features_array)
        
        # Get predictions
        quality_prob = self.model.predict_proba(features_scaled)[0][1]
        quality_score = float(quality_prob)
        
        # Calculate additional scores
        authenticity_score = self._calculate_authenticity_score(text)
        sentiment = self._determine_sentiment(text)
        complexity_score = self._calculate_complexity_score(text)
        uniqueness_score = self._calculate_uniqueness_score(text)
        spam_probability = self._calculate_spam_probability(text)
        
        # Generate flags
        flags = self._generate_flags(text, quality_score, spam_probability)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(quality_score, authenticity_score, spam_probability, flags)
        
        return CommentAnalysisResponse(
            comment_id=request.comment_id,
            quality_score=quality_score,
            authenticity_score=authenticity_score,
            sentiment=sentiment,
            complexity_score=complexity_score,
            uniqueness_score=uniqueness_score,
            spam_probability=spam_probability,
            reasoning=reasoning,
            flags=flags if flags else None
        )
    
    def _calculate_authenticity_score(self, text: str) -> float:
        """Calculate authenticity score based on various factors"""
        score = 0.5  # Base score
        
        # Check for natural language patterns
        words = text.split()
        if len(words) > 0:
            # Check for proper sentence structure
            if any(word.endswith('.') or word.endswith('!') or word.endswith('?') for word in words):
                score += 0.1
            
            # Check for varied word lengths
            word_lengths = [len(word) for word in words]
            if len(set(word_lengths)) > len(word_lengths) * 0.3:
                score += 0.1
            
            # Check for natural capitalization
            if any(word[0].isupper() for word in words if len(word) > 0):
                score += 0.1
        
        # Penalize excessive special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            score -= 0.2
        
        # Penalize excessive repetition
        if len(text) > 10:
            for i in range(len(text) - 3):
                if text[i:i+3] == text[i]*3:
                    score -= 0.3
                    break
        
        return max(0.0, min(1.0, score))
    
    def _determine_sentiment(self, text: str) -> str:
        """Determine sentiment of the text"""
        positive_words = ['good', 'great', 'awesome', 'amazing', 'love', 'like', 'excellent', 'wonderful', 'fantastic', 'brilliant']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'horrible', 'worst', 'disgusting', 'annoying', 'stupid']
        
        words = [word.lower() for word in text.split()]
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate complexity score"""
        words = text.split()
        if not words:
            return 0.0
        
        # Average word length
        avg_word_length = np.mean([len(word) for word in words])
        
        # Unique word ratio
        unique_words = len(set(word.lower() for word in words))
        unique_ratio = unique_words / len(words)
        
        # Sentence structure (simplified)
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Combine factors
        complexity = (avg_word_length / 10) * 0.4 + unique_ratio * 0.4 + (avg_sentence_length / 20) * 0.2
        
        return min(1.0, complexity)
    
    def _calculate_uniqueness_score(self, text: str) -> float:
        """Calculate uniqueness score"""
        words = [word.lower() for word in text.split()]
        if not words:
            return 0.0
        
        unique_words = len(set(words))
        total_words = len(words)
        
        return unique_words / total_words
    
    def _calculate_spam_probability(self, text: str) -> float:
        """Calculate spam probability"""
        spam_indicators = [
            'click here', 'buy now', 'free money', 'win prize', 'limited time',
            'act now', 'don\'t miss', 'exclusive offer', 'guaranteed', 'no risk'
        ]
        
        text_lower = text.lower()
        spam_count = sum(1 for indicator in spam_indicators if indicator in text_lower)
        
        # Check for excessive punctuation
        punctuation_ratio = sum(1 for c in text if c in string.punctuation) / len(text)
        
        # Check for excessive capitalization
        uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text)
        
        # Calculate spam probability
        spam_prob = min(1.0, (spam_count * 0.3) + (punctuation_ratio * 2) + (uppercase_ratio * 1.5))
        
        return spam_prob
    
    def _generate_flags(self, text: str, quality_score: float, spam_probability: float) -> List[str]:
        """Generate flags for the comment"""
        flags = []
        
        if quality_score < 0.3:
            flags.append('low_quality')
        
        if spam_probability > 0.7:
            flags.append('spam_detected')
        
        if len(text) < 10:
            flags.append('too_short')
        
        if len(text) > 500:
            flags.append('too_long')
        
        # Check for excessive special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            flags.append('excessive_special_chars')
        
        # Check for repetitive content
        if len(text) > 10:
            for i in range(len(text) - 4):
                if text[i:i+4] == text[i]*4:
                    flags.append('repetitive_content')
                    break
        
        return flags
    
    def _generate_reasoning(self, quality_score: float, authenticity_score: float, spam_probability: float, flags: List[str]) -> str:
        """Generate human-readable reasoning"""
        reasoning = f"Comment analysis completed. Quality score: {quality_score:.2f}, "
        reasoning += f"Authenticity: {authenticity_score:.2f}, Spam probability: {spam_probability:.2f}. "
        
        if flags:
            reasoning += f"Flags detected: {', '.join(flags)}. "
        
        if quality_score >= 0.7:
            reasoning += "High quality comment with good authenticity."
        elif quality_score >= 0.4:
            reasoning += "Medium quality comment with acceptable authenticity."
        else:
            reasoning += "Low quality comment with potential authenticity issues."
        
        return reasoning
