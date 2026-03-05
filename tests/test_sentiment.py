"""
tests/test_sentiment.py — Tests for sentiment analysis module.

HuggingFace Transformers are MOCKED so tests run instantly without
downloading models or requiring a GPU / internet connection.

Test coverage:
  - Positive sentiment detection
  - Negative sentiment detection
  - Distress keyword detection (keyword-based, not ML)
  - Emotion inference
  - Empty input handling
  - Model error fallback
"""

from unittest.mock import patch, MagicMock


# ── Helpers ────────────────────────────────────────────────────────────────

def make_pipeline_mock(label="NEGATIVE", score=0.95):
    """
    Return a mock that behaves like transformers.pipeline().
    When called with a string, returns [{"label": label, "score": score}].
    """
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = [{"label": label, "score": score}]
    return mock_pipeline


# ── Tests ──────────────────────────────────────────────────────────────────

class TestAnalyzeSentiment:

    @patch("app.ai_engine.sentiment._get_pipeline")
    def test_positive_sentiment(self, mock_get_pipeline):
        """Happy text should be classified as POSITIVE with joy emotion."""
        mock_get_pipeline.return_value = make_pipeline_mock("POSITIVE", 0.98)

        from app.ai_engine.sentiment import analyze_sentiment
        result = analyze_sentiment("I feel wonderful today, everything is great!")

        assert result["sentiment"] == "POSITIVE"
        assert result["emotion"] == "joy"
        assert result["distress_signal"] is False
        assert result["confidence"] > 0.5

    @patch("app.ai_engine.sentiment._get_pipeline")
    def test_negative_sentiment(self, mock_get_pipeline):
        """Sad text should be classified as NEGATIVE."""
        mock_get_pipeline.return_value = make_pipeline_mock("NEGATIVE", 0.91)

        from app.ai_engine.sentiment import analyze_sentiment
        result = analyze_sentiment("I feel really sad and miserable today.")

        assert result["sentiment"] == "NEGATIVE"
        assert result["distress_signal"] is False

    @patch("app.ai_engine.sentiment._get_pipeline")
    def test_distress_keyword_detected(self, mock_get_pipeline):
        """
        Explicit crisis keywords should trigger distress_signal=True
        REGARDLESS of the ML model's sentiment label.
        """
        # Model says positive (simulating underreporting), but keyword is present
        mock_get_pipeline.return_value = make_pipeline_mock("POSITIVE", 0.55)

        from app.ai_engine.sentiment import analyze_sentiment
        result = analyze_sentiment("I want to kill myself")

        assert result["distress_signal"] is True

    @patch("app.ai_engine.sentiment._get_pipeline")
    def test_anxiety_emotion_inferred(self, mock_get_pipeline):
        """Text with anxiety keywords should have emotion='anxiety'."""
        mock_get_pipeline.return_value = make_pipeline_mock("NEGATIVE", 0.88)

        from app.ai_engine.sentiment import analyze_sentiment
        result = analyze_sentiment("I feel so anxious and nervous about everything.")

        assert result["emotion"] == "anxiety"

    def test_empty_input_returns_neutral(self):
        """Empty string should return a neutral result without calling the model."""
        from app.ai_engine.sentiment import analyze_sentiment
        result = analyze_sentiment("")

        assert result["sentiment"] == "NEUTRAL"
        assert result["distress_signal"] is False

    def test_whitespace_input_returns_neutral(self):
        """Whitespace-only string treated as empty."""
        from app.ai_engine.sentiment import analyze_sentiment
        result = analyze_sentiment("   ")
        assert result["sentiment"] == "NEUTRAL"

    @patch("app.ai_engine.sentiment._get_pipeline")
    def test_model_error_falls_back_gracefully(self, mock_get_pipeline):
        """
        If the ML pipeline raises an exception, analyze_sentiment should
        NOT crash — it returns a fallback dict with error key.
        """
        mock_pipeline = MagicMock()
        mock_pipeline.side_effect = RuntimeError("Model exploded!")
        mock_get_pipeline.return_value = mock_pipeline

        from app.ai_engine.sentiment import analyze_sentiment
        result = analyze_sentiment("Normal text here.")

        assert "error" in result
        assert result["sentiment"] == "UNKNOWN"
        # Keyword check still runs in fallback
        assert isinstance(result["distress_signal"], bool)


class TestDetectDistress:
    """Unit tests for the distress keyword detector."""

    def test_explicit_suicidal_phrase(self):
        from app.ai_engine.sentiment import detect_distress
        assert detect_distress("I want to end my life") is True

    def test_normal_text_no_distress(self):
        from app.ai_engine.sentiment import detect_distress
        assert detect_distress("I had a nice walk in the park today.") is False

    def test_case_insensitive(self):
        from app.ai_engine.sentiment import detect_distress
        assert detect_distress("I AM FEELING HOPELESS") is True

    def test_empty_text(self):
        from app.ai_engine.sentiment import detect_distress
        assert detect_distress("") is False
