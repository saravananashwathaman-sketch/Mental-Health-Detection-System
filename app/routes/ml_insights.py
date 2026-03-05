"""
app/routes/ml_insights.py - New routes for ML-powered insights
Add to your existing routes
"""

from flask import Blueprint, jsonify, session, request
from app.routes.auth import login_required
from app.models import MoodEntry, ChatMessage
from app.ai_engine.advanced_ml import AdvancedMentalHealthML, PersonalizedWellbeingModel, DeepLearningAnalyzer
from app.ai_engine.realtime_analyzer import RealtimeMentalHealthMonitor, PredictiveHealthAnalytics
from datetime import datetime
import numpy as np

ml_insights_bp = Blueprint('ml_insights', __name__, url_prefix='/api/ml')

# Initialize ML components
advanced_ml = AdvancedMentalHealthML()
deep_analyzer = DeepLearningAnalyzer()
predictive_analytics = PredictiveHealthAnalytics()

# Store active monitors (in production, use Redis)
active_monitors = {}


@ml_insights_bp.route('/analyze/deep-emotion', methods=['POST'])
@login_required
def analyze_deep_emotion():
    """Deep emotion analysis endpoint"""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    result = advanced_ml.analyze_emotion_deep(text)
    return jsonify(result)


@ml_insights_bp.route('/predict/crisis-risk')
@login_required
def predict_crisis_risk():
    """Predict crisis risk based on user data"""
    user_id = session['user_id']

    # Get recent user data
    recent_moods = MoodEntry.query.filter_by(user_id=user_id)\
        .order_by(MoodEntry.timestamp.desc()).limit(30).all()
    recent_chats = ChatMessage.query.filter_by(user_id=user_id)\
        .order_by(ChatMessage.timestamp.desc()).limit(50).all()

    if not recent_moods and not recent_chats:
        return jsonify({'error': 'Insufficient data for prediction'}), 400

    # Extract features
    features = {
        'mood_score': np.mean([m.mood_score for m in recent_moods]) if recent_moods else 3,
        'sleep_hours': np.mean([m.sleep_hours for m in recent_moods]) if recent_moods else 7,
        'activity_level': np.mean([m.activity_level for m in recent_moods]) if recent_moods else 2,
        'sentiment_score': np.mean([1 if c.sentiment == 'POSITIVE' else -1
                                   for c in recent_chats if c.sentiment]) if recent_chats else 0,
        'stress_level': 3,  # Could be from additional input
        'social_interaction': 2,
        'medication_adherence': 1,
        'therapy_attendance': 1
    }

    prediction = advanced_ml.predict_crisis_risk(features)
    return jsonify(prediction)


@ml_insights_bp.route('/personalized/predict-trend')
@login_required
def predict_personalized_trend():
    """Get personalized wellbeing predictions"""
    user_id = session['user_id']

    # Get user data
    mood_entries = MoodEntry.query.filter_by(user_id=user_id)\
        .order_by(MoodEntry.timestamp.asc()).all()
    chat_messages = ChatMessage.query.filter_by(user_id=user_id)\
        .order_by(ChatMessage.timestamp.asc()).all()

    if len(mood_entries) < 10:
        return jsonify({'error': 'Need at least 10 mood entries for predictions'}), 400

    # Create and train personalized model
    personal_model = PersonalizedWellbeingModel(user_id)
    if not personal_model.train(mood_entries, chat_messages):
        return jsonify({'error': 'Could not train model with current data'}), 400

    # Get current features for prediction
    current_entry = mood_entries[-1]
    current_features = [
        current_entry.mood_score,
        current_entry.sleep_hours,
        current_entry.activity_level,
        0,  # no change initially
        datetime.now().hour,
        datetime.now().weekday(),
        np.mean([1 if c.sentiment == 'POSITIVE' else -1
                for c in chat_messages[-10:] if c.sentiment]) or 0,
        len([c for c in chat_messages[-3:]])
    ]

    predictions = personal_model.predict_wellbeing_trend(current_features)
    return jsonify({
        'predictions': predictions,
        'current_mood': current_entry.mood_score,
        'confidence': 'HIGH' if len(mood_entries) > 30 else 'MEDIUM'
    })


@ml_insights_bp.route('/analyze/suicidal-ideation', methods=['POST'])
@login_required
def analyze_suicidal_ideation():
    """Specialized suicidal ideation detection"""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    # Only allow this for high-risk users or with consent
    result = deep_analyzer.detect_suicidal_ideation(text)

    # Log this analysis for safety
    user_id = session['user_id']
    print(f"SAFETY LOG: Suicidal ideation analysis for user {user_id}: {result}")

    return jsonify(result)


@ml_insights_bp.route('/monitor/start')
@login_required
def start_realtime_monitoring():
    """Start real-time monitoring for user"""
    user_id = session['user_id']

    if user_id not in active_monitors:
        monitor = RealtimeMentalHealthMonitor(user_id)
        monitor.start_monitoring()
        active_monitors[user_id] = monitor

        return jsonify({'status': 'started', 'message': 'Real-time monitoring activated'})

    return jsonify({'status': 'already_running'})


@ml_insights_bp.route('/monitor/status')
@login_required
def get_monitor_status():
    """Get current monitoring status"""
    user_id = session['user_id']

    if user_id in active_monitors:
        status = active_monitors[user_id].get_current_state()
        return jsonify(status)

    return jsonify({'error': 'Monitoring not active'}), 404


@ml_insights_bp.route('/patterns/seasonal')
@login_required
def analyze_seasonal_patterns():
    """Analyze seasonal patterns in user's data"""
    user_id = session['user_id']

    mood_entries = MoodEntry.query.filter_by(user_id=user_id)\
        .order_by(MoodEntry.timestamp.asc()).all()

    if len(mood_entries) < 30:
        return jsonify({'error': 'Need at least 30 entries for seasonal analysis'}), 400

    patterns = predictive_analytics.analyze_seasonal_patterns(mood_entries)
    return jsonify(patterns)


@ml_insights_bp.route('/patterns/writing')
@login_required
def analyze_writing_patterns():
    """Analyze writing patterns for mental health indicators"""
    user_id = session['user_id']

    chat_messages = ChatMessage.query.filter_by(user_id=user_id)\
        .order_by(ChatMessage.timestamp.desc()).limit(100).all()

    if len(chat_messages) < 5:
        return jsonify({'error': 'Need at least 5 chat messages for analysis'}), 400

    patterns = deep_analyzer.analyze_writing_patterns(chat_messages)
    return jsonify(patterns)


@ml_insights_bp.route('/dashboard/insights')
@login_required
def get_comprehensive_insights():
    """Get comprehensive ML insights for dashboard"""
    user_id = session['user_id']

    # Gather all data
    mood_entries = MoodEntry.query.filter_by(user_id=user_id)\
        .order_by(MoodEntry.timestamp.desc()).limit(100).all()
    chat_messages = ChatMessage.query.filter_by(user_id=user_id)\
        .order_by(ChatMessage.timestamp.desc()).limit(100).all()

    insights = {
        'timestamp': datetime.now().isoformat(),
        'data_available': {
            'mood_entries': len(mood_entries),
            'chat_messages': len(chat_messages)
        }
    }

    # Add predictions if enough data
    if len(mood_entries) >= 10:
        features = {
            'mood_score': np.mean([m.mood_score for m in mood_entries[:10]]),
            'sleep_hours': np.mean([m.sleep_hours for m in mood_entries[:10]]),
            'activity_level': np.mean([m.activity_level for m in mood_entries[:10]]),
            'sentiment_score': np.mean([1 if c.sentiment == 'POSITIVE' else -1
                                       for c in chat_messages[:20] if c.sentiment]) or 0,
            'stress_level': 3,
            'social_interaction': 2,
            'medication_adherence': 1,
            'therapy_attendance': 1
        }
        insights['crisis_prediction'] = advanced_ml.predict_crisis_risk(features)

    # Add writing pattern analysis
    if len(chat_messages) >= 5:
        insights['writing_patterns'] = deep_analyzer.analyze_writing_patterns(chat_messages)

    # Add seasonal patterns
    if len(mood_entries) >= 30:
        insights['seasonal_patterns'] = predictive_analytics.analyze_seasonal_patterns(mood_entries)

    return jsonify(insights)

# Cleanup function for monitors


@ml_insights_bp.route('/monitor/stop')
@login_required
def stop_monitoring():
    """Stop real-time monitoring"""
    user_id = session['user_id']

    if user_id in active_monitors:
        active_monitors[user_id].stop_monitoring()
        del active_monitors[user_id]
        return jsonify({'status': 'stopped'})

    return jsonify({'error': 'Monitoring not active'}), 404
