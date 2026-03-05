"""
app/routes/dashboard.py — Dashboard blueprint.

Routes:
  GET /dashboard          → main dashboard page (score, risk, trends)
  GET /api/mood-data      → JSON data for Chart.js charts
"""

from datetime import datetime, timedelta, UTC
from flask import Blueprint, render_template, jsonify, session
from app.models import DailyScore, MoodEntry, ChatMessage
from app.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    """
    Render the dashboard with:
      - Latest wellbeing score and risk level
      - Recent mood entries (last 7)
      - Recent chat message count
    """
    user_id = session["user_id"]

    # Latest daily score
    latest_score = (
        DailyScore.query
        .filter_by(user_id=user_id)
        .order_by(DailyScore.timestamp.desc())
        .first()
    )

    # Last 7 mood entries for summary table
    recent_moods = (
        MoodEntry.query
        .filter_by(user_id=user_id)
        .order_by(MoodEntry.timestamp.desc())
        .limit(7)
        .all()
    )

    # Chat activity count (last 7 days)
    week_ago = datetime.now(UTC) - timedelta(days=7)
    chat_count = (
        ChatMessage.query
        .filter_by(user_id=user_id)
        .filter(ChatMessage.timestamp >= week_ago)
        .count()
    )

    return render_template(
        "dashboard/index.html",
        latest_score=latest_score,
        recent_moods=recent_moods,
        chat_count=chat_count,
    )


@dashboard_bp.route("/api/mood-data")
@login_required
def mood_data():
    """
    JSON endpoint used by Chart.js on the dashboard.

    Returns last 14 days of wellbeing scores and mood entries for
    the trend line chart and the doughnut score widget.

    Response:
      {
        "labels":           ["Mar 1", "Mar 2", …],
        "wellbeing_scores": [72.5, 68.0, …],
        "mood_scores":      [4, 3, …],
        "risk_levels":      ["GREEN", "AMBER", …]
      }
    """
    user_id = session["user_id"]
    two_weeks_ago = datetime.now(UTC) - timedelta(days=14)

    daily_scores = (
        DailyScore.query
        .filter_by(user_id=user_id)
        .filter(DailyScore.timestamp >= two_weeks_ago)
        .order_by(DailyScore.timestamp.asc())
        .all()
    )

    mood_entries = (
        MoodEntry.query
        .filter_by(user_id=user_id)
        .filter(MoodEntry.timestamp >= two_weeks_ago)
        .order_by(MoodEntry.timestamp.asc())
        .all()
    )

    return jsonify({
        "wellbeing": {
            "labels": [s.timestamp.strftime("%b %d") for s in daily_scores],
            "scores": [s.wellbeing_score for s in daily_scores],
            "risk_levels": [s.risk_level for s in daily_scores],
        },
        "mood": {
            "labels": [m.timestamp.strftime("%b %d") for m in mood_entries],
            "scores": [m.mood_score for m in mood_entries],
            "sleep":  [m.sleep_hours for m in mood_entries],
        },
    })
