"""
app/models.py — SQLAlchemy database models.

Models:
  - User         : account + consent
  - MoodEntry    : daily mood check-in data
  - ChatMessage  : conversation log with sentiment/emotion
  - DailyScore   : computed wellbeing score + risk level
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """
    Represents a registered user of the system.
    `consent_given` must be True before any data is stored (GDPR/ethics).
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    consent_given = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())

    # Profile Info for Assessment
    age_group = db.Column(db.String(50), nullable=True)   # Under 13, 13-17, etc.
    life_stage = db.Column(db.String(100), nullable=True)  # Student, Professional, etc.
    industry = db.Column(db.String(100), nullable=True)   # Optional (for working professionals)

    # Relationships (cascade delete — removing a user removes all their data)
    mood_entries = db.relationship(
        "MoodEntry", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    chat_messages = db.relationship(
        "ChatMessage", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    daily_scores = db.relationship(
        "DailyScore", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    assessment_sessions = db.relationship(
        "AssessmentSession", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    color_mood_tests = db.relationship(
        "ColorMoodTest", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    image_emotion_tests = db.relationship(
        "ImageEmotionTest", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    mental_health_reports = db.relationship(
        "MentalHealthReport", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """Hash and store password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class MoodEntry(db.Model):
    """
    Stores a single daily mood check-in submission.

    mood_score    : 1 (very low) to 5 (very high)
    sleep_hours   : hours slept last night (0.0–24.0)
    activity_level: 1 (sedentary), 2 (moderate), 3 (active)
    """

    __tablename__ = "mood_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)       # 1–5
    sleep_hours = db.Column(db.Float, nullable=False)        # 0–24
    activity_level = db.Column(db.Integer, nullable=False)   # 1–3
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "mood_score": self.mood_score,
            "sleep_hours": self.sleep_hours,
            "activity_level": self.activity_level,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return f"<MoodEntry user={self.user_id} mood={self.mood_score}>"


class ChatMessage(db.Model):
    """
    Stores an individual chat turn (user message + AI response).
    Includes NLP analysis results: sentiment, emotion, distress flag.
    """

    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=True)   # POSITIVE / NEGATIVE
    emotion = db.Column(db.String(50), nullable=True)     # joy, sadness, anger, …
    distress_flag = db.Column(db.Boolean, default=False)  # True if crisis detected
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_message": self.user_message,
            "ai_response": self.ai_response,
            "sentiment": self.sentiment,
            "emotion": self.emotion,
            "distress_flag": self.distress_flag,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return f"<ChatMessage {self.id} (user:{self.user_id})>"


class MediaContent(db.Model):
    """
    Model for professional media content (songs, reels, memes, etc).
    """
    __tablename__ = "media_content"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # song/video/image/meme/template
    personality_category = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.String(200))  # comma separated
    thumbnail_url = db.Column(db.String(500))
    language = db.Column(db.String(50), default="English")
    license = db.Column(db.String(100))
    fetched_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<MediaContent {self.title} ({self.type})>"


class ImagePool(db.Model):
    """Pool of 50+ images for the MCQ mood test."""
    __tablename__ = "image_pool"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    emotion_category = db.Column(db.String(50), nullable=False) # happy, sad, etc.
    score = db.Column(db.Integer, nullable=False)                # positive=3, neutral=2, negative=1, risk=0
    description = db.Column(db.String(200))

    def __repr__(self):
        return f"<ImagePool {self.id} {self.emotion_category}>"


class DailyScore(db.Model):
    """
    Computed wellbeing score for a user on a given day.

    wellbeing_score : 0 (worst) to 100 (best)
    risk_level      : GREEN (stable), AMBER (moderate concern), RED (high risk)
    """

    __tablename__ = "daily_scores"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    wellbeing_score = db.Column(db.Float, nullable=False)   # 0–100
    risk_level = db.Column(db.String(10), nullable=False)   # GREEN / AMBER / RED
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "wellbeing_score": self.wellbeing_score,
            "risk_level": self.risk_level,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return f"<DailyScore user={self.user_id} score={self.wellbeing_score} risk={self.risk_level}>"


class AssessmentQuestion(db.Model):
    """
    Stores a single mental health MCQ for the dynamic assessment.
    """
    __tablename__ = "assessment_questions"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False, index=True)  # Teenager, College, Professional, etc.
    question_text = db.Column(db.Text, nullable=False)

    # JSON-encoded options and their scores
    # Example: ["Almost never", "Sometimes", ...] and [3, 2, ...]
    options_json = db.Column(db.Text, nullable=False)
    scores_json = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<AssessmentQuestion {self.id} cat={self.category}>"


class AssessmentSession(db.Model):
    """
    Tracks a single completed assessment session and its summary result.
    """
    __tablename__ = "assessment_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    mood_prediction = db.Column(db.String(100))  # Positive, Mild Stress, etc.
    insights = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(), index=True)

    responses = db.relationship(
        "AssessmentResponse", backref="session", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AssessmentSession {self.id} user={self.user_id} mood={self.mood_prediction}>"


class AssessmentResponse(db.Model):
    """
    Stores an individual answer within an assessment session.
    Provides history to avoid repeating questions.
    """
    __tablename__ = "assessment_responses"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("assessment_sessions.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # Copied for easier lookup
    question_id = db.Column(db.Integer, db.ForeignKey("assessment_questions.id"), nullable=False)
    choice_index = db.Column(db.Integer, nullable=False)  # 0-3
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())

    def __repr__(self):
        return f"<AssessmentResponse user={self.user_id} question={self.question_id} score={self.score}>"


class ColorMoodTest(db.Model):
    """Stores results of the Color Mood MCQ test."""
    __tablename__ = "color_mood_tests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())

    def __repr__(self):
        return f"<ColorMoodTest user={self.user_id} color={self.color}>"


class ImageTestSession(db.Model):
    """Groups 3-7 image questions into a single session."""
    __tablename__ = "image_test_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_score = db.Column(db.Integer, default=0)
    question_count = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(), index=True)

    responses = db.relationship(
        "ImageEmotionTest", backref="session", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ImageTestSession {self.id} user={self.user_id} completed={self.is_completed}>"


class ImageEmotionTest(db.Model):
    """Stores individual answers for an Image MCQ test session."""
    __tablename__ = "image_emotion_tests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("image_test_sessions.id"), nullable=True) # Optional back-compatibility
    image_idx = db.Column(db.Integer, db.ForeignKey("image_pool.id"), nullable=False)
    emotion_category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())

    def __repr__(self):
        return f"<ImageEmotionTest user={self.user_id} category={self.emotion_category}>"


class MentalHealthReport(db.Model):
    """Unified report combining all signals."""
    __tablename__ = "mental_health_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    phq9_score = db.Column(db.Integer)
    gad7_score = db.Column(db.Integer)
    sentiment_score = db.Column(db.Float)
    color_score = db.Column(db.Integer)
    color_name = db.Column(db.String(50))
    color_hex = db.Column(db.String(20))
    image_score = db.Column(db.Integer)
    image_max = db.Column(db.Integer, default=3)
    overall_score = db.Column(db.Float)
    risk_level = db.Column(db.String(50))
    category = db.Column(db.String(100))
    concerns = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())

    def __repr__(self):
        return f"<MentalHealthReport user={self.user_id} risk={self.risk_level}>"

class VoiceEmotionEvent(db.Model):
    """Stores timeline events for the Voice Assistant's acoustic emotion analysis."""
    __tablename__ = "voice_emotion_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.String(100), nullable=True, index=True) # E.g., a timestamp hash for a single chat session
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(), index=True)
    detected_emotion = db.Column(db.String(50), nullable=False) # Calm, Anxious, etc.
    confidence_score = db.Column(db.Float, nullable=False, default=0.0)
    acoustic_features = db.Column(db.Text, nullable=True) # JSON dump of pitch, energy, etc.

    user = db.relationship("User", backref="voice_events")

    def __repr__(self):
        return f"<VoiceEmotionEvent user={self.user_id} emotion={self.detected_emotion}>"

class SystemInteractionInsight(db.Model):
    """Global Self-Learning model. Does not link to users to preserve privacy."""
    __tablename__ = "system_interaction_insights"

    id = db.Column(db.Integer, primary_key=True)
    intervention_type = db.Column(db.String(100), nullable=False, unique=True) # e.g. "breathing_protocol"
    usage_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<SystemInsight {self.intervention_type} success={self.success_count}/{self.usage_count}>"
