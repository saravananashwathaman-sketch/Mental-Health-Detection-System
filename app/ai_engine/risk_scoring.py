"""
app/ai_engine/risk_scoring.py — Rule-based mental health risk scoring engine.

Combines:
  - Mood score (user-reported, 1–5)
  - Sleep hours (last night)
  - Activity level (1–3)
  - Sentiment from recent chat messages
  - Distress signal flags from chat analysis

Outputs:
  - wellbeing_score : float 0–100 (higher = better)
  - risk_level      : "GREEN" | "AMBER" | "RED"

Risk thresholds:
  GREEN  score >= 70  (stable — no action needed)
  AMBER  score 40–69  (moderate concern — encourage check-in)
  RED    score < 40   (high risk — show crisis resources)
        *Also RED if any distress_signal was flagged in recent messages
"""

from typing import Optional

# ── Scoring weights ────────────────────────────────────────────────────────
# Each factor contributes a weighted sub-score that sums to 100 at maximum.
WEIGHTS = {
    "mood":       35,   # dominant factor — user's self-reported mood
    "sleep":      30,   # sleep is strongly correlated with mental health
    "activity":   15,   # physical activity contributes positively
    "sentiment":  20,   # NLP-derived signal from chat history
}

# ── Optimal sleep target ───────────────────────────────────────────────────
OPTIMAL_SLEEP_HOURS = 8.0
SLEEP_TOLERANCE = 2.5   # hours within which sleep is considered "good"


def _score_mood(mood_score: int) -> float:
    """
    Convert 1–5 mood rating to a 0–1 proportion.

    Args:
        mood_score: Integer 1 (very low) to 5 (very high).

    Returns:
        float 0.0–1.0
    """
    return max(0.0, min(1.0, (mood_score - 1) / 4))


def _score_sleep(sleep_hours: float) -> float:
    """
    Score sleep based on deviation from the 7–9 hour healthy range.

    Args:
        sleep_hours: Hours of sleep (float).

    Returns:
        float 0.0–1.0 — 1.0 for optimal, degrades with deviation.
    """
    deviation = abs(sleep_hours - OPTIMAL_SLEEP_HOURS)
    # Score drops linearly from 1.0 at deviation=0 to 0 at deviation >= SLEEP_TOLERANCE*2
    score = max(0.0, 1.0 - deviation / (SLEEP_TOLERANCE * 2))
    return score


def _score_activity(activity_level: int) -> float:
    """
    Convert 1–3 activity level to a 0–1 proportion.

    Args:
        activity_level: 1 (sedentary), 2 (moderate), 3 (active).

    Returns:
        float 0.0–1.0
    """
    return max(0.0, min(1.0, (activity_level - 1) / 2))


def _score_sentiment(
    recent_sentiments: list,
    distress_flags: list,
) -> float:
    """
    Compute a sentiment sub-score from recent chat analysis results.

    Args:
        recent_sentiments: List of "POSITIVE" | "NEGATIVE" | "NEUTRAL" strings
                           from the last N chat messages.
        distress_flags   : List of booleans indicating distress per message.

    Returns:
        float 0.0–1.0 — 1.0 if all positive, 0.0 if all negative + distress.
    """
    if not recent_sentiments:
        return 0.5  # neutral default when no chat history exists

    score = 0.0
    for s in recent_sentiments:
        if s == "POSITIVE":
            score += 1.0
        elif s == "NEUTRAL":
            score += 0.5
        elif s == "NEGATIVE":
            score += 0.0

    base_score = score / len(recent_sentiments)

    # Apply distress penalty — each distress flag reduces the score
    distress_count = sum(1 for d in distress_flags if d)
    penalty = min(0.4, distress_count * 0.15)

    return max(0.0, base_score - penalty)


def compute_wellbeing_score(
    mood_score: int,
    sleep_hours: float,
    activity_level: int,
    recent_sentiments: Optional[list] = None,
    distress_flags: Optional[list] = None,
) -> dict:
    """
    Main scoring function — combines all factors into a single wellbeing score.

    Args:
        mood_score        : int 1–5 (user's self-reported mood)
        sleep_hours       : float hours of sleep last night
        activity_level    : int 1–3 (activity level)
        recent_sentiments : list of sentiment strings from recent chats
        distress_flags    : list of bool distress flags from recent chats

    Returns:
        dict with:
          - wellbeing_score : float 0–100
          - risk_level      : "GREEN" | "AMBER" | "RED"
          - breakdown       : dict of individual sub-scores (for transparency)
    """
    if recent_sentiments is None:
        recent_sentiments = []
    if distress_flags is None:
        distress_flags = []

    # Compute normalised sub-scores (0–1)
    mood_norm = _score_mood(mood_score)
    sleep_norm = _score_sleep(sleep_hours)
    activity_norm = _score_activity(activity_level)
    sentiment_norm = _score_sentiment(recent_sentiments, distress_flags)

    # Weighted sum → 0–100 scale
    raw_score = (
        mood_norm * WEIGHTS["mood"] +
        sleep_norm * WEIGHTS["sleep"] +
        activity_norm * WEIGHTS["activity"] +
        sentiment_norm * WEIGHTS["sentiment"]
    )
    wellbeing_score = round(raw_score, 1)

    # ── Risk classification ─────────────────────────────────────────────────
    # Any distress flag immediately escalates to RED regardless of score.
    has_distress = any(distress_flags)

    if has_distress or wellbeing_score < 25:
        risk_level = "RED"
        # Cap score to max 24.0 if escalated by distress flag to avoid confusing user
        if wellbeing_score >= 25:
            wellbeing_score = 24.0
    elif wellbeing_score < 75:
        risk_level = "AMBER"
    else:
        risk_level = "GREEN"

    return {
        "wellbeing_score": wellbeing_score,
        "risk_level": risk_level,
        "breakdown": {
            "mood_contribution":      round(mood_norm * WEIGHTS["mood"], 1),
            "sleep_contribution":     round(sleep_norm * WEIGHTS["sleep"], 1),
            "activity_contribution":  round(activity_norm * WEIGHTS["activity"], 1),
            "sentiment_contribution": round(sentiment_norm * WEIGHTS["sentiment"], 1),
        },
    }


def classify_risk(wellbeing_score: float, has_distress: bool = False) -> str:
    """
    Classify risk level from a pre-computed score.

    Args:
        wellbeing_score : float 0–100
        has_distress    : bool — True forces RED classification

    Returns:
        "GREEN" | "AMBER" | "RED"
    """
    if has_distress or wellbeing_score < 40:
        return "RED"
    elif wellbeing_score < 70:
        return "AMBER"
    return "GREEN"
