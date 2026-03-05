"""
app/ai_engine/advanced_ml.py - Advanced ML models for enhanced predictions
Adds deep learning capabilities to your existing sentiment analysis
"""

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
from transformers import pipeline
import torch


class AdvancedMentalHealthML:
    """Advanced ML models for mental health prediction"""

    def __init__(self):
        self.models_dir = 'ml_models'
        os.makedirs(self.models_dir, exist_ok=True)

        # Load pre-trained models or initialize new ones
        self.crisis_predictor = self._load_or_create_model('crisis_predictor.pkl')
        self.wellbeing_predictor = self._load_or_create_model('wellbeing_predictor.pkl')
        self.scaler = StandardScaler()

        # Advanced transformer models (lazy loading)
        self.emotion_classifier = None
        self.depression_detector = None

    def _load_or_create_model(self, filename):
        """Load existing model or create new one"""
        path = os.path.join(self.models_dir, filename)
        if os.path.exists(path):
            return joblib.load(path)
        return None

    def _init_transformer_models(self):
        """Initialize transformer models (loaded on demand)"""
        if self.emotion_classifier is None:
            self.emotion_classifier = pipeline(
                "text-classification",
                model="bhadresh-savani/distilbert-base-uncased-emotion",
                return_all_scores=True
            )
        if self.depression_detector is None:
            self.depression_detector = pipeline(
                "text-classification",
                model="arpanghoshal/EmoRoBERTa",
                return_all_scores=True
            )

    def analyze_emotion_deep(self, text):
        """
        Deep emotion analysis using transformer models
        Returns fine-grained emotions with confidence scores
        """
        self._init_transformer_models()

        # Get emotion predictions
        emotions = self.emotion_classifier(text[:512])[0]

        # Map to your existing emotion categories
        emotion_map = {
            'joy': 'joy',
            'sadness': 'sadness',
            'anger': 'anger',
            'fear': 'anxiety',
            'love': 'joy',
            'surprise': 'neutral'
        }

        # Get top 3 emotions
        top_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)[:3]

        return {
            'primary_emotion': emotion_map.get(top_emotions[0]['label'], 'neutral'),
            'primary_confidence': top_emotions[0]['score'],
            'secondary_emotion': emotion_map.get(top_emotions[1]['label'], 'neutral'),
            'secondary_confidence': top_emotions[1]['score'],
            'all_emotions': {e['label']: e['score'] for e in emotions}
        }

    def predict_crisis_risk(self, user_features):
        """
        Predict crisis risk using ensemble methods
        Combines multiple signals for early warning
        """
        features = np.array([[
            user_features.get('mood_score', 3),
            user_features.get('sleep_hours', 7),
            user_features.get('activity_level', 2),
            user_features.get('sentiment_score', 0.5),
            user_features.get('stress_level', 3),
            user_features.get('social_interaction', 2),
            user_features.get('medication_adherence', 1),
            user_features.get('therapy_attendance', 1)
        ]])

        if self.crisis_predictor is None:
            # Return rule-based prediction if model not trained
            return self._rule_based_crisis_risk(features[0])

        # Scale features
        features_scaled = self.scaler.fit_transform(features)

        # Get prediction probabilities
        risk_proba = self.crisis_predictor.predict_proba(features_scaled)[0]

        return {
            'risk_probability': float(max(risk_proba)),
            'risk_level': 'HIGH' if risk_proba[1] > 0.7 else 'MEDIUM' if risk_proba[1] > 0.4 else 'LOW',
            'confidence': float(risk_proba[1])
        }

    def _rule_based_crisis_risk(self, features):
        """Fallback rule-based risk assessment"""
        mood, sleep, activity, sentiment = features[:4]

        # Simple weighted scoring
        score = (mood * 0.3) + (sleep/8 * 0.2) + (activity/3 * 0.2) + (sentiment * 0.3)

        if score < 2:
            return {'risk_probability': 0.85, 'risk_level': 'HIGH', 'confidence': 0.7}
        elif score < 3:
            return {'risk_probability': 0.45, 'risk_level': 'MEDIUM', 'confidence': 0.6}
        else:
            return {'risk_probability': 0.15, 'risk_level': 'LOW', 'confidence': 0.8}


class PersonalizedWellbeingModel:
    """Personalized ML model per user for better predictions"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1
        )
        self.is_trained = False

    def prepare_features(self, mood_entries, chat_messages):
        """
        Prepare feature vector from user history
        """
        features = []
        targets = []

        # Extract temporal patterns
        for i in range(1, len(mood_entries)):
            entry = mood_entries[i]
            prev_entry = mood_entries[i-1]

            # Features
            feat = [
                prev_entry.mood_score,
                prev_entry.sleep_hours,
                prev_entry.activity_level,
                entry.mood_score - prev_entry.mood_score,  # mood change
                entry.timestamp.hour,  # time of day
                entry.timestamp.weekday(),  # day of week
            ]

            # Add chat sentiment features if available
            recent_chats = [c for c in chat_messages
                            if c.timestamp.date() == entry.timestamp.date()]
            if recent_chats:
                sentiments = [1 if c.sentiment == 'POSITIVE' else -1
                              for c in recent_chats if c.sentiment]
                feat.append(np.mean(sentiments) if sentiments else 0)
                feat.append(len(recent_chats))
            else:
                feat.extend([0, 0])

            features.append(feat)
            targets.append(entry.mood_score)

        return np.array(features), np.array(targets)

    def train(self, mood_entries, chat_messages):
        """Train personalized model for user"""
        if len(mood_entries) < 10:
            return False  # Need at least 10 entries

        X, y = self.prepare_features(mood_entries, chat_messages)
        if len(X) > 5:
            self.model.fit(X, y)
            self.is_trained = True
            return True
        return False

    def predict_wellbeing_trend(self, current_features):
        """
        Predict wellbeing score for next 7 days
        """
        if not self.is_trained:
            return None

        predictions = []
        current = current_features.copy()

        for day in range(7):
            pred = self.model.predict([current])[0]
            predictions.append({
                'day': day + 1,
                'predicted_mood': float(np.clip(pred, 1, 5)),
                'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d')
            })

            # Update features for next prediction
            current[2] = pred  # use predicted mood for next day
            current[3] = 0  # assume no change

        return predictions


class DeepLearningAnalyzer:
    """Deep learning models for pattern recognition"""

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.models = {}

    def detect_suicidal_ideation(self, text):
        """
        Specialized model for detecting suicidal ideation
        """
        # Load model if not already loaded
        if 'suicidal' not in self.models:
            self.models['suicidal'] = pipeline(
                "text-classification",
                model="cardiffnlp/twitter-roberta-base-suicide",
                device=0 if torch.cuda.is_available() else -1
            )

        result = self.models['suicidal'](text[:512])[0]

        return {
            'is_suicidal': result['label'] == 'suicide',
            'confidence': result['score'],
            'severity': 'CRITICAL' if result['score'] > 0.9 else 'HIGH' if result['score'] > 0.7 else 'MEDIUM'
        }

    def analyze_writing_patterns(self, user_messages):
        """
        Analyze writing patterns for mental health indicators
        """
        if len(user_messages) < 5:
            return None

        all_text = ' '.join([msg.user_message for msg in user_messages])

        # Linguistic analysis
        patterns = {
            'first_person_usage': all_text.count('i ') + all_text.count("i'm") + all_text.count("i've"),
            'negative_words': sum(1 for word in ['no', 'not', 'never', 'can\'t', 'won\'t'] if word in all_text.lower()),
            'positive_words': sum(1 for word in ['good', 'great', 'happy', 'love', 'wonderful'] if word in all_text.lower()),
            'question_marks': all_text.count('?'),
            'exclamation_marks': all_text.count('!'),
            'avg_sentence_length': len(all_text.split()) / max(1, all_text.count('.') + all_text.count('!') + all_text.count('?'))
        }

        # Pattern scoring
        risk_indicators = 0
        if patterns['first_person_usage'] > len(user_messages) * 2:
            risk_indicators += 1
        if patterns['negative_words'] > patterns['positive_words'] * 2:
            risk_indicators += 1
        if patterns['avg_sentence_length'] < 5:
            risk_indicators += 1

        return {
            'patterns': patterns,
            'risk_indicators': risk_indicators,
            'overall_pattern_risk': 'HIGH' if risk_indicators >= 2 else 'MEDIUM' if risk_indicators >= 1 else 'LOW'
        }
