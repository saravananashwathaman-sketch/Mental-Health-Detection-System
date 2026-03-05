"""
app/ai_engine/llm_client.py — LLM wrapper for empathetic conversational responses.

Supports:
  - Groq (Llama 3) via the `groq` Python SDK
  - Google Gemini via `google-generativeai`

Provider is selected by the LLM_PROVIDER environment variable.
Falls back to a safe default response if no API key is configured.

SAFETY GUARDRAILS:
  - System prompt prohibits giving medical diagnoses or prescriptions.
  - If risk_level is RED, a crisis escalation message is appended.
  - All errors are caught; a fallback message is always returned.
"""

from flask import current_app

# ── System prompt ─────────────────────────────────────────────────────────
# This prompt is prepended to every conversation to enforce safe behaviour.
SYSTEM_PROMPT = """You are a compassionate mental health support companion.
Your role is to listen, empathise, and offer gentle emotional support.

STRICT RULES — you MUST follow these at all times:
1. You are NOT a therapist, doctor, or medical professional.
2. NEVER diagnose any mental health condition.
3. NEVER prescribe medication or specific treatments.
4. NEVER minimise someone's pain or feelings.
5. Always validate feelings before offering coping suggestions.
6. Keep responses warm, concise (2–4 sentences), and non-judgmental.
7. You MUST ALWAYS speak and respond strictly in English, regardless of what language the user speaks. Do NOT use Tamil or any other language.
8. If the user seems in serious distress, encourage professional help.
9. When appropriate, suggest helpful media content (songs, videos, or motivational clips). 
   You have access to a curated list of content:
   - "Enjoy Enjaami" (Tamil Indie/Calm): https://www.youtube.com/watch?v=eYq7WapuDLU
   - "Arabic Kuthu" (Viral/Energetic): https://www.youtube.com/watch?v=KVP9TfP_69w
   - "The Power of Habit" (Motivational): https://www.youtube.com/watch?v=PZ7lDrwYdZc
   - "96 Movie Medley" (Nostalgic): https://www.youtube.com/watch?v=l_S78v_B_t0
   Ensure you provide the full link when suggesting.

This system is for early emotional support detection only — not a medical tool."""


def _build_crisis_message() -> str:
    """Build crisis message dynamically from the central helplines config."""
    from app.helplines import HELPLINES
    lines = [
        "\n\n---",
        "🆘 **It seems you may be going through a really difficult time.**",
        "Please reach out to a crisis helpline immediately:\n",
    ]
    for h in HELPLINES:
        if h.get("number"):
            lines.append(f"- **{h['name']}:** {h['display']}  {('(' + h['hours'] + ')') if h.get('hours') else ''}")
        elif h.get("url"):
            lines.append(f"- **{h['name']}:** {h['url']}")
    return "\n".join(lines)

def _get_dynamic_system_prompt() -> str:
    """Appends Global Self-Learning insights to the base prompt."""
    prompt = SYSTEM_PROMPT
    try:
        from app.models import SystemInteractionInsight
        insights = SystemInteractionInsight.query.filter(SystemInteractionInsight.success_count > 0).order_by(SystemInteractionInsight.success_count.desc()).limit(2).all()
        if insights:
            prompt += "\n\n💡 SYSTEM LEARNING INSIGHTS (Globally successful strategies to suggest):\n"
            for ins in insights:
                prompt += f"- Recommend {ins.intervention_type.replace('_', ' ')} (Proven effective {ins.success_count} times globally).\n"
    except Exception as e:
        pass # Ignore db errors during prompt build
    return prompt

# ── Fallback response (no API key configured) ──────────────────────────────
FALLBACK_RESPONSE = (
    "I'm here to listen and support you. While I'm unable to respond "
    "with full AI capabilities right now, please know that your feelings are "
    "valid. If you're struggling, consider talking to a trusted friend, "
    "family member, or a mental health professional."
)


def get_llm_response(
    user_message: str,
    conversation_history: list = None,
    risk_level: str = "GREEN",
) -> str:
    """
    Generate an empathetic AI response using the configured LLM provider.

    Args:
        user_message         : The user's latest message.
        conversation_history : List of dicts [{role, content}, …] for context.
        risk_level           : Current risk classification (GREEN/AMBER/RED).
                               RED triggers crisis resource injection.

    Returns:
        A string containing the AI's response.
    """
    if conversation_history is None:
        conversation_history = []

    provider = current_app.config.get("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        response = _groq_response(user_message, conversation_history)
    elif provider == "gemini":
        response = _gemini_response(user_message, conversation_history)
    else:
        response = FALLBACK_RESPONSE

    # Append crisis resources if the user is at high risk
    if risk_level == "RED":
        response += _build_crisis_message()

    return response


def _groq_response(user_message: str, history: list) -> str:
    """Call Groq Llama 3 API."""
    api_key = current_app.config.get("GROQ_API_KEY", "")
    if not api_key:
        return FALLBACK_RESPONSE

    try:
        from groq import Groq
        import httpx

        client = Groq(api_key=api_key, http_client=httpx.Client())

        # Build OpenAI-compatible messages list
        dynamic_prompt = _get_dynamic_system_prompt()
        messages = [{"role": "system", "content": dynamic_prompt}]
        for turn in history[-6:]:   # keep last 6 turns for context window
            messages.append(turn)
        messages.append({"role": "user", "content": user_message})

        chat_completion = client.chat.completions.create(
            messages=messages,
            model=current_app.config.get("GROQ_MODEL", "llama3-8b-8192"),
            max_tokens=300,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content.strip()

    except Exception as exc:
        return f"{FALLBACK_RESPONSE}\n\n*(Groq API error: {exc})*"


def _gemini_response(user_message: str, history: list) -> str:
    """Call Google Gemini API."""
    api_key = current_app.config.get("GEMINI_API_KEY", "")
    if not api_key:
        return FALLBACK_RESPONSE

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=current_app.config.get("GEMINI_MODEL", "gemini-1.5-flash"),
            system_instruction=SYSTEM_PROMPT,
        )

        # Convert history to Gemini format
        gemini_history = []
        for turn in history[-6:]:
            role = "user" if turn["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [turn["content"]]})

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(user_message)
        return response.text.strip()

    except Exception as exc:
        return f"{FALLBACK_RESPONSE}\n\n*(Gemini API error: {exc})*"
