"""
app/routes/mood.py — Mood check-in blueprint.

Routes:
  GET  /mood          → render daily check-in form
  POST /mood          → process submission, compute risk score, store results
  GET  /wellness      → wellness hub page (breathing, grounding, resources)
"""

from datetime import timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash
)
from app import db
from app.models import MoodEntry, ChatMessage, DailyScore
from app.routes.auth import login_required

mood_bp = Blueprint("mood", __name__)


@mood_bp.route("/mood", methods=["GET", "POST"])
@login_required
def checkin():
    """
    GET  → render the mood check-in form.
    POST → validate, store MoodEntry, compute wellbeing score, store DailyScore.
    """
    user_id = session["user_id"]

    if request.method == "POST":
        try:
            mood_score = int(request.form.get("mood_score", 3))
            sleep_hours = float(request.form.get("sleep_hours", 7.0))
            activity_level = int(request.form.get("activity_level", 2))
            notes = request.form.get("notes", "").strip()
        except (ValueError, TypeError):
            flash("Invalid input. Please fill in all fields correctly.", "danger")
            return redirect(url_for("mood.checkin"))

        # Clamp values to valid ranges
        mood_score = max(1, min(5, mood_score))
        sleep_hours = max(0.0, min(24.0, sleep_hours))
        activity_level = max(1, min(3, activity_level))

        # ── Gather recent chat sentiment for risk scoring ──────────────────
        recent_chats = (
            ChatMessage.query
            .filter_by(user_id=user_id)
            .order_by(ChatMessage.timestamp.desc())
            .limit(10)
            .all()
        )
        recent_sentiments = [m.sentiment for m in recent_chats if m.sentiment]
        distress_flags = [m.distress_flag for m in recent_chats]

        # ── Compute wellbeing score ────────────────────────────────────────
        from app.ai_engine.risk_scoring import compute_wellbeing_score
        result = compute_wellbeing_score(
            mood_score=mood_score,
            sleep_hours=sleep_hours,
            activity_level=activity_level,
            recent_sentiments=recent_sentiments,
            distress_flags=distress_flags,
        )

        # ── Store MoodEntry ───────────────────────────────────────────────
        entry = MoodEntry(
            user_id=user_id,
            mood_score=mood_score,
            sleep_hours=sleep_hours,
            activity_level=activity_level,
            notes=notes,
        )
        db.session.add(entry)

        # ── Store DailyScore ──────────────────────────────────────────────
        daily = DailyScore(
            user_id=user_id,
            wellbeing_score=result["wellbeing_score"],
            risk_level=result["risk_level"],
        )
        db.session.add(daily)
        db.session.commit()

        risk = result["risk_level"]
        score = result["wellbeing_score"]

        if risk == "RED":
            flash(
                f"Your wellbeing score is {score}/100 (High Risk). "
                "Please visit the Wellness Hub for support resources.",
                "danger",
            )
        elif risk == "AMBER":
            flash(
                f"Your wellbeing score is {score}/100 (Moderate concern). "
                "Remember to take care of yourself today.",
                "warning",
            )
        else:
            flash(
                f"Your wellbeing score is {score}/100 (Stable). Keep it up! 🌱",
                "success",
            )

        return redirect(url_for("dashboard.index"))

    return render_template("mood/checkin.html")


@mood_bp.route("/wellness")
@login_required
def wellness():
    """Render the Wellness Hub with coping resources."""
    return render_template("wellness/hub.html")


@mood_bp.route("/mood/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit(entry_id):
    """Edit an existing mood entry."""
    entry = MoodEntry.query.get_or_404(entry_id)

    # Ensure user owns this entry
    if entry.user_id != session["user_id"]:
        flash("You don't have permission to edit this entry.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        try:
            mood_score = int(request.form.get("mood_score", 3))
            sleep_hours = float(request.form.get("sleep_hours", 7.0))
            activity_level = int(request.form.get("activity_level", 2))
            notes = request.form.get("notes", "").strip()
        except (ValueError, TypeError):
            flash("Invalid input. Please fill in all fields correctly.", "danger")
            return redirect(url_for("mood.edit", entry_id=entry.id))

        # Clamp values to valid ranges
        entry.mood_score = max(1, min(5, mood_score))
        entry.sleep_hours = max(0.0, min(24.0, sleep_hours))
        entry.activity_level = max(1, min(3, activity_level))
        entry.notes = notes

        # Set up for recomputing score
        from app.ai_engine.risk_scoring import compute_wellbeing_score

        # Gather recent chat sentiment for risk scoring (same as checkin)
        user_id = session["user_id"]
        recent_chats = (
            ChatMessage.query
            .filter_by(user_id=user_id)
            .order_by(ChatMessage.timestamp.desc())
            .limit(10)
            .all()
        )
        recent_sentiments = [m.sentiment for m in recent_chats if m.sentiment]
        distress_flags = [m.distress_flag for m in recent_chats]

        # Compute new wellbeing score based on edited input
        result = compute_wellbeing_score(
            mood_score=entry.mood_score,
            sleep_hours=entry.sleep_hours,
            activity_level=entry.activity_level,
            recent_sentiments=recent_sentiments,
            distress_flags=distress_flags,
        )

        # ── Update DailyScore ──────────────────────────────────────────────
        # Look for a DailyScore created around the same time as this entry
        # usually they are created on the same day
        start_of_day = entry.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        daily = DailyScore.query.filter(
            DailyScore.user_id == user_id,
            DailyScore.timestamp >= start_of_day
        ).order_by(DailyScore.timestamp.desc()).first()

        if daily:
            daily.wellbeing_score = result["wellbeing_score"]
            daily.risk_level = result["risk_level"]
        else:
            # Fallback if no daily score exists for that day somehow
            daily = DailyScore(
                user_id=user_id,
                wellbeing_score=result["wellbeing_score"],
                risk_level=result["risk_level"],
            )
            db.session.add(daily)

        db.session.commit()

        flash("Check-in updated successfully.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("mood/edit.html", entry=entry)


@mood_bp.route("/mood/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete(entry_id):
    """Delete a mood entry."""
    entry = MoodEntry.query.get_or_404(entry_id)

    user_id = session["user_id"]

    # Ensure user owns this entry
    if entry.user_id != user_id:
        flash("You don't have permission to delete this entry.", "danger")
        return redirect(url_for("dashboard.index"))

    start_of_day = entry.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    db.session.delete(entry)
    db.session.commit()

    # ── Update or Delete DailyScore ──────────────────────────────────────────────
    # Check if there are other check-ins for the same day
    other_entries = MoodEntry.query.filter(
        MoodEntry.user_id == user_id,
        MoodEntry.timestamp >= start_of_day,
        MoodEntry.timestamp < start_of_day + timedelta(days=1)
    ).order_by(MoodEntry.timestamp.desc()).all()

    daily = DailyScore.query.filter(
        DailyScore.user_id == user_id,
        DailyScore.timestamp >= start_of_day,
        DailyScore.timestamp < start_of_day + timedelta(days=1)
    ).first()

    if other_entries and daily:
        # Recompute score based on the latest entry of the day
        latest_entry = other_entries[0]

        from app.ai_engine.risk_scoring import compute_wellbeing_score

        recent_chats = (
            ChatMessage.query
            .filter_by(user_id=user_id)
            .order_by(ChatMessage.timestamp.desc())
            .limit(10)
            .all()
        )
        recent_sentiments = [m.sentiment for m in recent_chats if m.sentiment]
        distress_flags = [m.distress_flag for m in recent_chats]

        result = compute_wellbeing_score(
            mood_score=latest_entry.mood_score,
            sleep_hours=latest_entry.sleep_hours,
            activity_level=latest_entry.activity_level,
            recent_sentiments=recent_sentiments,
            distress_flags=distress_flags,
        )

        daily.wellbeing_score = result["wellbeing_score"]
        daily.risk_level = result["risk_level"]
        db.session.commit()
    elif not other_entries and daily:
        # No other entries for the day, delete the daily score row
        db.session.delete(daily)
        db.session.commit()

    flash("Check-in deleted.", "success")
    return redirect(url_for("dashboard.index"))
