"""
tests/test_risk_scoring.py — Tests for the rule-based risk scoring engine.

All tests run without any API calls (pure Python logic only).

Test coverage:
  - GREEN classification  (high mood + good sleep + positive sentiment)
  - AMBER classification  (moderate inputs)
  - RED classification    (low mood + poor sleep + negative sentiment)
  - Distress signal force-escalates to RED regardless of score
  - Score is within 0–100 range
  - classify_risk() helper function
"""

import pytest
from app.ai_engine.risk_scoring import compute_wellbeing_score, classify_risk


class TestWellbeingScore:
    """Tests for compute_wellbeing_score()."""

    def test_score_in_valid_range(self):
        """Score must always be between 0 and 100."""
        result = compute_wellbeing_score(3, 7.0, 2)
        assert 0 <= result["wellbeing_score"] <= 100

    def test_green_classification(self):
        """
        HIGH mood + optimal sleep + active + positive chats → GREEN (≥70).
        """
        result = compute_wellbeing_score(
            mood_score=5,
            sleep_hours=8.0,
            activity_level=3,
            recent_sentiments=["POSITIVE", "POSITIVE", "POSITIVE"],
            distress_flags=[False, False, False],
        )
        assert result["risk_level"] == "GREEN"
        assert result["wellbeing_score"] >= 70, (
            f"Expected score ≥70 for optimal inputs, got {result['wellbeing_score']}"
        )

    def test_amber_classification(self):
        """
        MODERATE inputs (mid-range mood, slight sleep deficit) → AMBER (40–69).
        """
        result = compute_wellbeing_score(
            mood_score=3,
            sleep_hours=5.5,
            activity_level=1,
            recent_sentiments=["NEGATIVE", "POSITIVE"],
            distress_flags=[False, False],
        )
        assert result["risk_level"] == "AMBER"
        assert 40 <= result["wellbeing_score"] < 70, (
            f"Expected score 40–69, got {result['wellbeing_score']}"
        )

    def test_red_classification_low_inputs(self):
        """
        Very LOW mood + bad sleep + sedentary + negative chats → RED (<40).
        """
        result = compute_wellbeing_score(
            mood_score=1,
            sleep_hours=2.0,
            activity_level=1,
            recent_sentiments=["NEGATIVE", "NEGATIVE", "NEGATIVE"],
            distress_flags=[False, False, False],
        )
        assert result["risk_level"] == "RED"
        assert result["wellbeing_score"] < 40, (
            f"Expected score <40 for minimal inputs, got {result['wellbeing_score']}"
        )

    def test_distress_flag_forces_red(self):
        """
        A distress signal MUST escalate risk to RED even if score is high.
        This ensures crisis keywords override a misleadingly good score.
        """
        result = compute_wellbeing_score(
            mood_score=5,
            sleep_hours=8.0,
            activity_level=3,
            recent_sentiments=["POSITIVE", "POSITIVE"],
            distress_flags=[False, True],   # ← one distress flag
        )
        assert result["risk_level"] == "RED", (
            "Distress signal should force RED classification regardless of score."
        )

    def test_no_chat_history_defaults_neutral(self):
        """When no chat history is provided, sentiment defaults to 0.5 (neutral)."""
        result_no_history = compute_wellbeing_score(
            mood_score=3, sleep_hours=7.0, activity_level=2
        )
        result_neutral = compute_wellbeing_score(
            mood_score=3, sleep_hours=7.0, activity_level=2,
            recent_sentiments=[], distress_flags=[]
        )
        assert result_no_history["wellbeing_score"] == result_neutral["wellbeing_score"]

    def test_breakdown_keys_present(self):
        """Result must include a 'breakdown' dict with the four contribution keys."""
        result = compute_wellbeing_score(3, 7.0, 2)
        assert "breakdown" in result
        for key in ["mood_contribution", "sleep_contribution",
                    "activity_contribution", "sentiment_contribution"]:
            assert key in result["breakdown"]


class TestClassifyRisk:
    """Tests for the classify_risk() helper."""

    @pytest.mark.parametrize("score,expected", [
        (100, "GREEN"),
        (70,  "GREEN"),
        (69,  "AMBER"),
        (40,  "AMBER"),
        (39,  "RED"),
        (0,   "RED"),
    ])
    def test_boundary_scores(self, score, expected):
        assert classify_risk(score) == expected, (
            f"classify_risk({score}) should be {expected}"
        )

    def test_distress_overrides_green(self):
        """Even a perfect score should be RED when distress=True."""
        assert classify_risk(100.0, has_distress=True) == "RED"

    def test_distress_overrides_amber(self):
        assert classify_risk(55.0, has_distress=True) == "RED"
