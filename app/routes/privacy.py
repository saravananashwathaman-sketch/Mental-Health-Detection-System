"""
app/routes/privacy.py — Privacy / data control blueprint.

Routes:
  GET  /privacy         → privacy policy + data control page
  POST /privacy/delete  → permanently delete ALL user data
  GET  /privacy/export  → download JSON export of all user data
"""

import json
from datetime import datetime, UTC
from flask import (
    Blueprint, render_template, redirect, url_for, session,
    flash, make_response
)
from app import db
from app.models import User, MoodEntry, ChatMessage, DailyScore
from app.routes.auth import login_required

privacy_bp = Blueprint("privacy", __name__, url_prefix="/privacy")


@privacy_bp.route("/")
@login_required
def index():
    """Render the privacy policy and data management page."""
    user_id = session["user_id"]
    user = db.session.get(User, user_id)

    # Summary counts for the data overview panel
    mood_count = MoodEntry.query.filter_by(user_id=user_id).count()
    chat_count = ChatMessage.query.filter_by(user_id=user_id).count()
    score_count = DailyScore.query.filter_by(user_id=user_id).count()

    return render_template(
        "privacy/index.html",
        user=user,
        mood_count=mood_count,
        chat_count=chat_count,
        score_count=score_count,
    )


@privacy_bp.route("/delete", methods=["POST"])
@login_required
def delete_data():
    """
    Permanently delete ALL data stored for the current user.
    This includes: mood entries, chat messages, daily scores, and the
    user account itself.

    After deletion, the session is cleared and the user is redirected
    to the registration page.
    """
    user_id = session["user_id"]
    user = db.session.get(User, user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    # Cascade deletes are configured on the model relationships,
    # so deleting the User row removes all related data automatically.
    db.session.delete(user)
    db.session.commit()

    session.clear()
    flash(
        "All your data has been permanently deleted. "
        "We hope you'll return when you're ready.",
        "info",
    )
    return redirect(url_for("auth.register"))


@privacy_bp.route("/export")
@login_required
def export_data():
    """
    Export all stored data as a downloadable JSON file.
    Gives users full transparency and GDPR-compliant data portability.
    """
    user_id = session["user_id"]
    user = db.session.get(User, user_id)

    mood_entries = MoodEntry.query.filter_by(user_id=user_id).all()
    chat_messages = ChatMessage.query.filter_by(user_id=user_id).all()
    daily_scores = DailyScore.query.filter_by(user_id=user_id).all()

    export = {
        "exported_at": datetime.now(UTC).isoformat(),
        "user": {
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "consent_given": user.consent_given,
        },
        "mood_entries": [m.to_dict() for m in mood_entries],
        "chat_messages": [c.to_dict() for c in chat_messages],
        "daily_scores": [s.to_dict() for s in daily_scores],
    }

    response = make_response(json.dumps(export, indent=2))
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=my_mental_health_data_{datetime.now(UTC).strftime('%Y%m%d')}.json"
    )
    return response
