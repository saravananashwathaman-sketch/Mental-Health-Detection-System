"""
app/ai_engine/sentiment.py — HuggingFace-powered sentiment & emotion analysis.

Uses DistilBERT fine-tuned on SST-2 for sentiment classification.
Adds distress signal detection via crisis keyword matching.

NOTE: On first run the model (~250 MB) will be downloaded from HuggingFace Hub
and cached in ~/.cache/huggingface. Subsequent runs use the local cache.
"""

import re

# Lazy import — transformer pipeline loaded on first use to avoid slowing
# application startup.
_sentiment_pipeline = None

# ── Crisis / distress keywords ─────────────────────────────────────────────
# Broad set covering explicit and implicit distress signals.
DISTRESS_KEYWORDS = [
    # Suicidal ideation
    "kill myself", "end my life", "want to die", "suicidal", "suicide",
    "don't want to live", "no reason to live", "better off dead",
    # Self-harm
    "hurt myself", "self harm", "cutting", "harming myself",
    # Hopelessness
    "no hope", "hopeless", "can't go on", "can't cope", "give up",
    "nothing matters", "pointless", "worthless", "i am worthless",
    # Crisis states
    "crisis", "emergency", "help me", "desperate", "unbearable",
    "can't take it anymore", "breaking down",
]

# Emotion mapping — maps negative sentiment to an inferred emotional label
# based on common linguistic patterns.
EMOTION_PATTERNS = {
    "sadness":    [r"\bsad\b", r"\bcry\b", r"\btears\b", r"\bdepressed\b",
                   r"\bgrief\b", r"\bmiserable\b", r"\bheartbroken\b"],
    "anxiety":    [r"\banxious\b", r"\bworried\b", r"\bnervous\b",
                   r"\bpanic\b", r"\bscared\b", r"\bfear\b", r"\bstress\b"],
    "anger":      [r"\bangry\b", r"\bfurious\b", r"\brage\b",
                   r"\bfrustrated\b", r"\bifuriated\b"],
    "hopelessness": [r"\bhopeless\b", r"\bgive up\b", r"\bno point\b",
                     r"\bworthless\b", r"\buseless\b"],
    "loneliness": [r"\blonely\b", r"\balone\b", r"\bisolated\b",
                   r"\bunderstood\b", r"\bno one\b"],
}


def _get_pipeline():
    """Lazily load the HuggingFace sentiment pipeline (singleton)."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            # Use CPU to avoid CUDA dependency issues on most machines
            device=-1,
        )
    return _sentiment_pipeline


def detect_distress(text: str) -> bool:
    """
    Check if the text contains explicit distress / crisis signals.

    Args:
        text: User message text.

    Returns:
        True if a distress keyword is detected, False otherwise.
    """
    text_lower = text.lower()
    return any(kw in text_lower for kw in DISTRESS_KEYWORDS)


def infer_emotion(text: str, sentiment_label: str) -> str:
    """
    Infer a fine-grained emotion label from the text and base sentiment.

    Args:
        text:            User message text.
        sentiment_label: "POSITIVE" or "NEGATIVE" from HuggingFace model.

    Returns:
        A string emotion label: joy | sadness | anxiety | anger |
        hopelessness | loneliness | neutral
    """
    text_lower = text.lower()

    if sentiment_label == "POSITIVE":
        return "joy"

    # Match against emotion patterns (order matters — first match wins)
    for emotion, patterns in EMOTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return emotion

    return "sadness"  # default for unmatched negative sentiment


def analyze_sentiment(text: str) -> dict:
    """
    Perform full sentiment & emotion analysis on a piece of text.

    Args:
        text: The user's message string.

    Returns:
        dict with keys:
          - sentiment       : "POSITIVE" or "NEGATIVE"
          - confidence      : float 0–1
          - emotion         : emotion label string
          - distress_signal : bool — True if crisis keywords detected
    """
    if not text or not text.strip():
        return {
            "sentiment": "NEUTRAL",
            "confidence": 1.0,
            "emotion": "neutral",
            "distress_signal": False,
        }

    try:
        pipe = _get_pipeline()
        # HuggingFace pipeline returns a list; take the first item
        result = pipe(text[:512])[0]   # truncate to model max length

        sentiment_label = result["label"]    # "POSITIVE" or "NEGATIVE"
        confidence = round(result["score"], 4)

        emotion = infer_emotion(text, sentiment_label)
        distress = detect_distress(text)

        # Override: distress detection always marks signal even if sentiment
        # classifier labels it POSITIVE (e.g., sarcastic/underreporting users)
        return {
            "sentiment": sentiment_label,
            "confidence": confidence,
            "emotion": emotion,
            "distress_signal": distress,
        }

    except Exception as exc:
        # Fallback — never crash the request pipeline due to NLP errors
        return {
            "sentiment": "UNKNOWN",
            "confidence": 0.0,
            "emotion": "unknown",
            "distress_signal": detect_distress(text),  # still do keyword check
            "error": str(exc),
        }
