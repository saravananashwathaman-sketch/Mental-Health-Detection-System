"""
app/routes/chat.py — Chat blueprint.

Routes:
  GET  /chat          → render chat interface
  POST /chat/send     → JSON API: receive user message, run NLP, call LLM,
                        store ChatMessage, return response + sentiment data
"""

from flask import (
    Blueprint, render_template, request, jsonify, session
)
from datetime import datetime
from app import db
from app.models import ChatMessage, DailyScore
from app.routes.auth import login_required
from app.ai_engine.sentiment import analyze_sentiment
from app.ai_engine.llm_client import get_llm_response

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/", methods=["GET"])
@login_required
def index():
    """Render the chat bubble UI with recent message history."""
    user_id = session["user_id"]
    # Load last 20 messages for initial render
    messages = (
        ChatMessage.query
        .filter_by(user_id=user_id)
        .order_by(ChatMessage.timestamp.asc())
        .limit(20)
        .all()
    )
    return render_template("chat/index.html", messages=messages)


@chat_bp.route("/voice", methods=["GET"])
@login_required
def voice():
    """Render the immersive AI Voice Avatar interface."""
    return render_template("chat/voice.html")


@chat_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    """
    JSON endpoint — receives user message and returns AI response.

    Request JSON:
      { "message": "I feel very anxious today" }

    Response JSON:
      {
        "ai_response": "...",
        "sentiment": "NEGATIVE",
        "emotion": "anxiety",
        "distress_flag": false,
        "risk_level": "AMBER"
      }
    """
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    acoustic_data = data.get("acoustic_features")

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # ── Step 1: Sentiment + distress analysis ──────────────────────────────
    try:
        nlp_result = analyze_sentiment(user_message)
    except Exception:
        nlp_result = {
            "sentiment": "UNKNOWN",
            "confidence": 0.0,
            "emotion": "unknown",
            "distress_signal": False,
        }

    # ── Step 1.5: Acoustic Emotion Heuristics ──────────────────────────────
    detected_emotion = "Neutral"
    if acoustic_data:
        pitch = acoustic_data.get("pitch", 0)
        energy = acoustic_data.get("energy", 0)
        speed = acoustic_data.get("speech_speed", 0)
        
        # Simple threshold heuristics for demonstration:
        # High pitch + High Energy + Fast + Negative NLP = Angry / Anxious
        # Low pitch + Low Energy + Slow + Negative NLP = Depressed / Sad
        # Variations mapped based on standard arousal/valence circles
        
        is_high_arousal = energy > 0.05 and speed > 0.1
        is_low_arousal = energy < 0.02 and speed < 0.05
        
        sentiment = nlp_result.get("sentiment", "UNKNOWN")
        
        if sentiment == "NEGATIVE":
            if is_high_arousal:
                detected_emotion = "Anxious" if pitch > 200 else "Angry"
            elif is_low_arousal:
                detected_emotion = "Depressed" if pitch < 100 else "Sad"
            else:
                detected_emotion = "Stressed"
        elif sentiment == "POSITIVE":
            if is_high_arousal:
                detected_emotion = "Happy"
            else:
                detected_emotion = "Calm"
        else:
            detected_emotion = "Neutral"
            
        # Log to Timeline
        import json
        from app.models import VoiceEmotionEvent
        v_event = VoiceEmotionEvent(
            user_id=user_id,
            timestamp=datetime.now(),
            detected_emotion=detected_emotion,
            confidence_score=0.85, # static mock for now
            acoustic_features=json.dumps(acoustic_data)
        )
        db.session.add(v_event)
        
        # ── Step 1.6: Global Self-Learning Assessment ─────────────────────
        # If the user shifted to 'Calm' or 'Happy', look if the previous AI msg offered an intervention
        if detected_emotion in ["Calm", "Happy"]:
            prev_msg = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp.desc()).first()
            if prev_msg:
                from app.models import SystemInteractionInsight
                if "breathe" in prev_msg.ai_response.lower() or "breathing" in prev_msg.ai_response.lower():
                    insight = SystemInteractionInsight.query.filter_by(intervention_type="breathing_exercises").first()
                    if insight:
                        insight.success_count += 1
                elif "mindful" in prev_msg.ai_response.lower() or "grounding" in prev_msg.ai_response.lower():
                    insight = SystemInteractionInsight.query.filter_by(intervention_type="mindfulness_grounding").first()
                    if insight:
                        insight.success_count += 1

    # ── Step 2: Determine current risk level for this user ─────────────────
    latest_score = (
        DailyScore.query
        .filter_by(user_id=user_id)
        .order_by(DailyScore.timestamp.desc())
        .first()
    )
    current_risk = latest_score.risk_level if latest_score else "GREEN"

    # Distress signal immediately elevates risk for crisis resource injection
    if nlp_result.get("distress_signal"):
        current_risk = "RED"

    # ── Step 3: Build conversation history for LLM context ────────────────
    recent_msgs = (
        ChatMessage.query
        .filter_by(user_id=user_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(6)
        .all()
    )
    history = []
    for msg in reversed(recent_msgs):
        history.append({"role": "user", "content": msg.user_message})
        history.append({"role": "assistant", "content": msg.ai_response})

    # ── Step 4: Call LLM ───────────────────────────────────────────────────
    try:
        ai_response = get_llm_response(
            user_message=user_message,
            conversation_history=history,
            risk_level=current_risk,
        )
    except Exception:
        ai_response = (
            "I'm here for you. I'm having a little trouble responding right "
            "now, but please know your feelings are important and valid."
        )

    # ── Step 4.5: Mood Test Recommendation Logic ──────────────────────────
    indicators = ["anxiety", "stress", "depression", "hopelessness", "lonely", "panic", "worthless"]
    indicator_count = 0
    
    # Check current message
    msg_lower = user_message.lower()
    for ind in indicators:
        if ind in msg_lower:
            indicator_count += 1
            
    # Check recent history for additional indicators
    for msg in recent_msgs:
        if msg.emotion and msg.emotion.lower() in indicators:
            indicator_count += 1
            
    if indicator_count >= 3:
        recommendation = "\n\nI recommend taking a quick [mood check test](/tests/color-test) to better understand your emotional state."
        if recommendation not in ai_response:
            ai_response += recommendation

    # Track Global Interventions Usage
    from app.models import SystemInteractionInsight
    if "breathe" in ai_response.lower() or "breathing" in ai_response.lower():
        insight = SystemInteractionInsight.query.filter_by(intervention_type="breathing_exercises").first()
        if not insight:
            insight = SystemInteractionInsight(intervention_type="breathing_exercises", usage_count=0, success_count=0)
            db.session.add(insight)
        insight.usage_count += 1
    if "mindful" in ai_response.lower() or "grounding" in ai_response.lower():
        insight = SystemInteractionInsight.query.filter_by(intervention_type="mindfulness_grounding").first()
        if not insight:
            insight = SystemInteractionInsight(intervention_type="mindfulness_grounding", usage_count=0, success_count=0)
            db.session.add(insight)
        insight.usage_count += 1

    # ── Step 5: Store the conversation turn ───────────────────────────────
    chat_msg = ChatMessage(
        user_id=user_id,
        user_message=user_message,
        ai_response=ai_response,
        sentiment=nlp_result.get("sentiment"),
        emotion=nlp_result.get("emotion"),
        distress_flag=nlp_result.get("distress_signal", False),
    )
    db.session.add(chat_msg)
    db.session.commit()

    return jsonify({
        "ai_response": ai_response,
        "sentiment": nlp_result.get("sentiment"),
        "emotion": nlp_result.get("emotion"),
        "distress_flag": nlp_result.get("distress_signal", False),
        "risk_level": current_risk,
    })
