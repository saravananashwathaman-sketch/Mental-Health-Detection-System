"""
app/ai_engine/realtime_analyzer.py - Real-time mental health monitoring
Adds streaming analysis capabilities to your chat
"""

import numpy as np
from collections import deque
from datetime import datetime, timedelta
from threading import Thread
import time


class RealtimeMentalHealthMonitor:
    """Real-time monitoring of mental health indicators"""

    def __init__(self, user_id, window_size=50):
        self.user_id = user_id
        self.window_size = window_size

        # Rolling windows for real-time analysis
        self.sentiment_window = deque(maxlen=window_size)
        self.emotion_window = deque(maxlen=window_size)
        self.response_time_window = deque(maxlen=20)
        self.message_length_window = deque(maxlen=window_size)

        # Alert thresholds
        self.thresholds = {
            'negative_sentiment_ratio': 0.6,
            'rapid_mood_swings': 2.0,  # standard deviations
            'response_time_anomaly': 3.0,  # seconds
            'crisis_keyword_frequency': 0.3
        }

        # Monitoring state
        self.is_monitoring = False
        self.alerts = []
        self.current_risk_score = 0

    def start_monitoring(self):
        """Start real-time monitoring thread"""
        self.is_monitoring = True
        self.monitor_thread = Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False

    def add_chat_interaction(self, message, sentiment, emotion, response_time):
        """Add new chat interaction to windows"""
        self.sentiment_window.append(1 if sentiment == 'POSITIVE' else -1 if sentiment == 'NEGATIVE' else 0)
        self.emotion_window.append(emotion)
        self.response_time_window.append(response_time)
        self.message_length_window.append(len(message))

        # Recalculate risk score
        self._update_risk_score()

    def _update_risk_score(self):
        """Update current risk score based on recent patterns"""
        if len(self.sentiment_window) < 10:
            return

        # Sentiment score (negative = higher risk)
        sentiment_score = 1 - (np.mean(self.sentiment_window) + 1) / 2

        # Volatility score (rapid changes = higher risk)
        if len(self.sentiment_window) > 5:
            volatility = np.std(list(self.sentiment_window)[-10:])
        else:
            volatility = 0

        # Crisis keywords score (from emotion window)
        crisis_emotions = ['sadness', 'anger', 'anxiety']
        crisis_ratio = sum(1 for e in list(self.emotion_window)[-10:]
                           if e in crisis_emotions) / min(10, len(self.emotion_window))

        # Combined score
        self.current_risk_score = (
            sentiment_score * 0.5 +
            volatility * 0.3 +
            crisis_ratio * 0.2
        ) * 100

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            time.sleep(5)  # Check every 5 seconds

            if len(self.sentiment_window) < 5:
                continue

            # Check for alert conditions
            alerts = self._check_alert_conditions()
            if alerts:
                self.alerts.extend(alerts)

    def _check_alert_conditions(self):
        """Check for various alert conditions"""
        alerts = []

        # Rapid negative sentiment
        recent_sentiments = list(self.sentiment_window)[-10:]
        if recent_sentiments and np.mean(recent_sentiments) < -0.5:
            alerts.append({
                'type': 'RAPID_NEGATIVE_SHIFT',
                'severity': 'HIGH',
                'message': 'Detected rapid shift to negative sentiment',
                'timestamp': datetime.now()
            })

        # Unusual response time patterns
        recent_response_times = list(self.response_time_window)[-10:]
        if recent_response_times:
            avg_time = np.mean(recent_response_times)
            if avg_time > self.thresholds['response_time_anomaly']:
                alerts.append({
                    'type': 'RESPONSE_TIME_ANOMALY',
                    'severity': 'MEDIUM',
                    'message': f'Unusual response time pattern detected: {avg_time:.1f}s avg',
                    'timestamp': datetime.now()
                })

        # Message length patterns (potential disengagement)
        recent_lengths = list(self.message_length_window)[-10:]
        if recent_lengths and len(recent_lengths) >= 5:
            if np.mean(recent_lengths) < 10 and len(recent_lengths) > 3:
                alerts.append({
                    'type': 'DISENGAGEMENT',
                    'severity': 'MEDIUM',
                    'message': 'User messages becoming very short - possible disengagement',
                    'timestamp': datetime.now()
                })

        return alerts

    def get_current_state(self):
        """Get current monitoring state"""
        return {
            'risk_score': self.current_risk_score,
            'active_alerts': len([a for a in self.alerts
                                 if a['timestamp'] > datetime.now() - timedelta(minutes=30)]),
            'sentiment_trend': list(self.sentiment_window)[-20:] if self.sentiment_window else [],
            'recent_alerts': self.alerts[-5:] if self.alerts else []
        }


class PredictiveHealthAnalytics:
    """Predictive analytics for mental health trends"""

    def __init__(self):
        self.patterns = {}

    def analyze_seasonal_patterns(self, mood_entries):
        """
        Analyze seasonal and temporal patterns in mood
        """
        if len(mood_entries) < 30:
            return None

        # Group by various time periods
        patterns = {
            'by_hour': {},
            'by_day': {},
            'by_month': {},
            'by_season': {'winter': [], 'spring': [], 'summer': [], 'fall': []}
        }

        for entry in mood_entries:
            hour = entry.timestamp.hour
            day = entry.timestamp.strftime('%A')
            month = entry.timestamp.month
            season = self._get_season(entry.timestamp)

            # Aggregate scores
            patterns['by_hour'][hour] = patterns['by_hour'].get(hour, []) + [entry.mood_score]
            patterns['by_day'][day] = patterns['by_day'].get(day, []) + [entry.mood_score]
            patterns['by_month'][month] = patterns['by_month'].get(month, []) + [entry.mood_score]
            patterns['by_season'][season].append(entry.mood_score)

        # Calculate averages
        for period in ['by_hour', 'by_day', 'by_month']:
            for key in patterns[period]:
                patterns[period][key] = np.mean(patterns[period][key])

        for season in patterns['by_season']:
            if patterns['by_season'][season]:
                patterns['by_season'][season] = np.mean(patterns['by_season'][season])
            else:
                patterns['by_season'][season] = None

        # Find best and worst periods
        best_hour = max(patterns['by_hour'].items(), key=lambda x: x[1])
        worst_hour = min(patterns['by_hour'].items(), key=lambda x: x[1])
        best_day = max(patterns['by_day'].items(), key=lambda x: x[1])
        worst_day = min(patterns['by_day'].items(), key=lambda x: x[1])

        return {
            'patterns': patterns,
            'insights': {
                'best_time': f"{best_hour[0]}:00 - Score: {best_hour[1]:.1f}",
                'worst_time': f"{worst_hour[0]}:00 - Score: {worst_hour[1]:.1f}",
                'best_day': f"{best_day[0]} - Score: {best_day[1]:.1f}",
                'worst_day': f"{worst_day[0]} - Score: {worst_day[1]:.1f}",
                'seasonal_trend': self._analyze_seasonal_trend(patterns['by_season'])
            }
        }

    def _get_season(self, date):
        """Determine season from date"""
        month = date.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'

    def _analyze_seasonal_trend(self, season_data):
        """Analyze seasonal patterns"""
        valid_seasons = {s: v for s, v in season_data.items() if v is not None}
        if len(valid_seasons) < 2:
            return "Insufficient data for seasonal analysis"

        max_season = max(valid_seasons.items(), key=lambda x: x[1])
        min_season = min(valid_seasons.items(), key=lambda x: x[1])

        return f"Best: {max_season[0]}, Most challenging: {min_season[0]}"
