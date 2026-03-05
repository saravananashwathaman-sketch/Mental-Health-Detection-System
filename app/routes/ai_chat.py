"""
app/routes/ai_chat.py — Dedicated /ai-chat endpoint.

Provides a clean, standalone REST API for the mental health chat assistant.
Works alongside the existing /chat blueprint without breaking any current features.

Endpoint:  POST /ai-chat
Auth:      Required (session-based, same as rest of app)
Request:   { "message": "I've been feeling really anxious lately" }
Response:  {
               "response":       "AI response text",
               "risk_level":     "low" | "moderate" | "high",
               "distress_flag":  true | false,
               "emotion":        "anxiety" | "sadness" | ...,
               "timestamp":      "2026-03-05T11:52:00"
           }

Risk levels:
  low       — Normal conversation, supportive responses
  moderate  — Concerning language, wellness tips recommended
  high      — Crisis keywords detected, professional help strongly encouraged
"""

from datetime import datetime, UTC
from flask import Blueprint, request, jsonify, session
from app import db
from app.models import ChatMessage
from app.routes.auth import login_required
from app.ai_engine.llm_client import get_llm_response

ai_chat_bp = Blueprint("ai_chat", __name__, url_prefix="/ai-chat")

# ── Distress keyword sets by severity ────────────────────────────────────────
HIGH_RISK_PHRASES = [
    "suicidal", "want to die", "end my life", "kill myself",
    "want to disappear", "hopeless", "no reason to live",
    "can't go on", "can't take it anymore", "better off dead",
]

MODERATE_RISK_PHRASES = [
    "can't handle this", "overwhelmed", "breaking down", "falling apart",
    "exhausted", "numb", "empty inside", "nobody cares", "worthless",
    "pointless", "anxious", "panic", "depressed", "can't cope",
]

# ── Emotion keyword mapping ───────────────────────────────────────────────────
EMOTION_KEYWORDS = {
    "anxiety":   ["anxious", "nervous", "panic", "worry", "scared", "fear"],
    "sadness":   ["sad", "depressed", "empty", "numb", "hopeless", "miserable", "cry"],
    "anger":     ["angry", "furious", "rage", "hate", "frustrated"],
    "loneliness": ["alone", "lonely", "isolated", "nobody", "no one"],
    "stress":    ["stressed", "overwhelmed", "pressure", "burnout"],
}


def detect_risk(message: str) -> tuple[str, bool]:
    """
    Scan message for distress signals.

    Returns:
        (risk_level, distress_flag)
        risk_level: "high" | "moderate" | "low"
        distress_flag: True if crisis keywords found
    """
    msg_lower = message.lower()

    for phrase in HIGH_RISK_PHRASES:
        if phrase in msg_lower:
            return "high", True

    for phrase in MODERATE_RISK_PHRASES:
        if phrase in msg_lower:
            return "moderate", False

    return "low", False


def detect_emotion(message: str) -> str:
    """Map message to the most likely emotion label."""
    msg_lower = message.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return emotion
    return "neutral"


def build_risk_prompt_hint(risk_level: str) -> str:
    """
    Return an extra system hint based on risk level so the LLM
    adapts its tone — injected into the user message context.
    """
    if risk_level == "high":
        return (
            "\n\n[SYSTEM HINT: This user may be in crisis. "
            "Respond with maximum empathy. Strongly encourage them to "
            "contact a mental health professional or crisis helpline immediately. "
            "Do NOT dismiss or minimise their pain.]"
        )
    if risk_level == "moderate":
        return (
            "\n\n[SYSTEM HINT: The user seems distressed. "
            "Offer gentle coping techniques such as deep breathing, "
            "journaling, or talking to someone trusted.]"
        )
    return ""


@ai_chat_bp.route("", methods=["POST"])
@login_required
def ai_chat():
    """
    POST /ai-chat
    Main chat endpoint. Analyzes user message for risk,
    calls Groq LLM, logs to DB, returns structured JSON.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Message is required"}), 400

    user_message = data["message"].strip()
    if len(user_message) > 2000:
        return jsonify({"error": "Message too long (max 2000 characters)"}), 400

    user_id = session.get("user_id")

    # ── Step 1: Risk & emotion detection ─────────────────────────────────────
    risk_level, distress_flag = detect_risk(user_message)
    emotion = detect_emotion(user_message)

    # ── Step 2: Build message with risk hint for better LLM response ─────────
    enhanced_message = user_message + build_risk_prompt_hint(risk_level)

    # ── Step 3: Fetch recent conversation history for context ────────────────
    recent_msgs = (
        ChatMessage.query
        .filter_by(user_id=user_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(6)
        .all()
    )
    history = []
    for msg in reversed(recent_msgs):
        history.append({"role": "user",      "content": msg.user_message})
        history.append({"role": "assistant", "content": msg.ai_response})

    # ── Step 4: Call Groq LLM ─────────────────────────────────────────────────
    try:
        ai_response = get_llm_response(
            user_message=enhanced_message,
            conversation_history=history,
            risk_level="RED" if distress_flag else ("AMBER" if risk_level == "moderate" else "GREEN"),
        )
    except Exception as exc:
        ai_response = (
            "I'm here for you. I'm having a small technical issue right now, "
            "but please know your feelings are valid. If you need immediate support, "
            f"please reach out to a crisis helpline.\n\n*(Error: {exc})*"
        )

    # ── Step 5: Persist to database ───────────────────────────────────────────
    try:
        msg_record = ChatMessage(
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response,
            sentiment="NEGATIVE" if risk_level in ("moderate", "high") else "POSITIVE",
            emotion=emotion,
            distress_flag=distress_flag,
        )
        db.session.add(msg_record)
        db.session.commit()
    except Exception:
        db.session.rollback()

    # ── Step 6: Return structured response ────────────────────────────────────
    return jsonify({
        "response":      ai_response,
        "risk_level":    risk_level,
        "distress_flag": distress_flag,
        "emotion":       emotion,
        "timestamp":     datetime.now(UTC).isoformat(),
    })
