"""
ml_model_trainer.py - Script to train ML models on historical data
Run periodically to update models with new data
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os
from datetime import datetime
from app import create_app
from app.models import User, MoodEntry, ChatMessage, DailyScore
import warnings
warnings.filterwarnings('ignore')


class ModelTrainer:
    def __init__(self):
        self.app = create_app()
        self.models_dir = 'ml_models'
        os.makedirs(self.models_dir, exist_ok=True)

    def prepare_training_data(self):
        """Prepare dataset from all users (anonymized)"""
        with self.app.app_context():
            # Get all users with sufficient data
            users = User.query.all()

            X = []  # Features
            y_crisis = []  # Crisis labels (binary)
            y_wellbeing = []  # Wellbeing scores (regression)

            for user in users:
                # Get user's data
                mood_entries = MoodEntry.query.filter_by(user_id=user.id)\
                    .order_by(MoodEntry.timestamp).all()
                chat_messages = ChatMessage.query.filter_by(user_id=user.id)\
                    .order_by(ChatMessage.timestamp).all()
                daily_scores = DailyScore.query.filter_by(user_id=user.id)\
                    .order_by(DailyScore.timestamp).all()

                if len(mood_entries) < 10 or len(daily_scores) < 10:
                    continue

                # Create sequences for training
                for i in range(10, len(mood_entries)):
                    # Features from last 10 entries
                    recent_moods = mood_entries[i-10:i]
                    # Calculate features
                    features = [
                        np.mean([m.mood_score for m in recent_moods]),
                        np.std([m.mood_score for m in recent_moods]),
                        np.mean([m.sleep_hours for m in recent_moods]),
                        np.std([m.sleep_hours for m in recent_moods]),
                        np.mean([m.activity_level for m in recent_moods]),
                        len([m for m in recent_moods if m.notes]),  # journaling frequency
                    ]

                    # Add chat features if available
                    recent_chats = [c for c in chat_messages
                                    if c.timestamp > mood_entries[i-10].timestamp]
                    if recent_chats:
                        sentiments = [1 if c.sentiment == 'POSITIVE' else -1
                                      for c in recent_chats if c.sentiment]
                        features.extend([
                            np.mean(sentiments) if sentiments else 0,
                            len(recent_chats),
                            sum(1 for c in recent_chats if c.distress_flag)
                        ])
                    else:
                        features.extend([0, 0, 0])

                    # Target: crisis label (1 if risk_level in next 7 days is RED)
                    next_week_scores = [s for s in daily_scores[i:i+7]
                                        if s.timestamp > mood_entries[i-1].timestamp]
                    crisis_target = 1 if any(s.risk_level == 'RED' for s in next_week_scores) else 0

                    # Wellbeing target: average wellbeing score next 7 days
                    wellbeing_target = np.mean([s.wellbeing_score for s in next_week_scores]) if next_week_scores else 50

                    X.append(features)
                    y_crisis.append(crisis_target)
                    y_wellbeing.append(wellbeing_target)

            return np.array(X), np.array(y_crisis), np.array(y_wellbeing)

    def train_crisis_predictor(self, X, y):
        """Train Random Forest for crisis prediction"""
        print(f"Training crisis predictor with {len(X)} samples...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )

        # Train model
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0)
        }

        print("Crisis Predictor Metrics:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.3f}")

        # Save model
        joblib.dump(model, os.path.join(self.models_dir, 'crisis_predictor.pkl'))

        # Save feature importance
        feature_importance = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(X.shape[1])],
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        feature_importance.to_csv(os.path.join(self.models_dir, 'feature_importance.csv'), index=False)

        return model, metrics

    def train_wellbeing_predictor(self, X, y):
        """Train Gradient Boosting for wellbeing prediction"""
        print(f"\nTraining wellbeing predictor with {len(X)} samples...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train model
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        model.fit(X_train, y_train)

        # Evaluate
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)

        print("Wellbeing Predictor R² Score:")
        print(f"  Train: {train_score:.3f}")
        print(f"  Test: {test_score:.3f}")

        # Save model
        joblib.dump(model, os.path.join(self.models_dir, 'wellbeing_predictor.pkl'))

        return model, {'train_r2': train_score, 'test_r2': test_score}

    def train_all_models(self):
        """Train all ML models"""
        print("=" * 50)
        print("Starting ML Model Training Pipeline")
        print("=" * 50)

        # Prepare data
        print("\n1. Preparing training data...")
        X, y_crisis, y_wellbeing = self.prepare_training_data()

        if len(X) == 0:
            print("No training data available. Add more users with sufficient history.")
            return

        print(f"   Training samples: {len(X)}")
        print(f"   Features: {X.shape[1]}")

        # Train crisis predictor
        print("\n2. Training Crisis Prediction Model...")
        crisis_model, crisis_metrics = self.train_crisis_predictor(X, y_crisis)

        # Train wellbeing predictor
        print("\n3. Training Wellbeing Prediction Model...")
        wellbeing_model, wellbeing_metrics = self.train_wellbeing_predictor(X, y_wellbeing)

        # Save training metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'samples': len(X),
            'features': X.shape[1],
            'crisis_metrics': crisis_metrics,
            'wellbeing_metrics': wellbeing_metrics,
            'crisis_distribution': {
                'negative': int(np.sum(y_crisis == 0)),
                'positive': int(np.sum(y_crisis == 1))
            }
        }

        import json
        with open(os.path.join(self.models_dir, 'training_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        print("\n" + "=" * 50)
        print("Training Complete!")
        print(f"Models saved to: {self.models_dir}")
        print("=" * 50)

        return metadata


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_all_models()
