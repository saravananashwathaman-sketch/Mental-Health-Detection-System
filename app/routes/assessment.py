"""
app/routes/assessment.py — Mental Health Assessment & Profiling flow.
"""

import json
import random
from flask import Blueprint, render_template, request, redirect, url_for, session
from app import db
from app.models import User, AssessmentQuestion, AssessmentSession, AssessmentResponse
from app.routes.auth import login_required

assessment_bp = Blueprint("assessment", __name__, url_prefix="/assessment")


@assessment_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Step-by-step profiling to determine question category."""
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        age_group = request.form.get("age_group")
        life_stage = request.form.get("life_stage")
        industry = request.form.get("industry", "")

        user.age_group = age_group
        user.life_stage = life_stage
        user.industry = industry
        db.session.commit()

        return redirect(url_for("assessment.start_session"))

    return render_template("assessment/profile.html")


@assessment_bp.route("/start")
@login_required
def start_session():
    """Initialize a new assessment session."""
    user = User.query.get(session["user_id"])
    if not user.age_group or not user.life_stage:
        return redirect(url_for("assessment.profile"))

    # Determine category based on profile
    category = _determine_category(user)

    # Create session
    new_session = AssessmentSession(
        user_id=user.id,
        category=category,
        total_score=0,
        max_score=0
    )
    db.session.add(new_session)
    db.session.commit()

    session["assessment_id"] = new_session.id
    session["question_index"] = 0

    # Select 10-15 random questions from the category that the user hasn't seen
    seen_ids = [r.question_id for r in AssessmentResponse.query.filter_by(user_id=user.id).all()]

    questions = AssessmentQuestion.query.filter_by(category=category).filter(~AssessmentQuestion.id.in_(seen_ids)).all()

    if len(questions) < 10:
        # Fallback: if we've run out of new questions in this category, reuse others
        questions = AssessmentQuestion.query.filter_by(category=category).all()

    selected_questions = random.sample(questions, min(10, len(questions)))
    session["assessment_questions"] = [q.id for q in selected_questions]

    return redirect(url_for("assessment.take_question"))


@assessment_bp.route("/question", methods=["GET", "POST"])
@login_required
def take_question():
    """Display and process a single MCQ."""
    assessment_id = session.get("assessment_id")
    q_ids = session.get("assessment_questions", [])
    idx = session.get("question_index", 0)

    if not assessment_id or idx >= len(q_ids):
        return redirect(url_for("assessment.results"))

    question = AssessmentQuestion.query.get(q_ids[idx])
    options = json.loads(question.options_json)

    if request.method == "POST":
        choice = int(request.form.get("choice"))
        scores = json.loads(question.scores_json)
        selected_score = scores[choice]

        # Record response
        resp = AssessmentResponse(
            session_id=assessment_id,
            user_id=session["user_id"],
            question_id=question.id,
            choice_index=choice,
            score=selected_score
        )
        db.session.add(resp)

        # Update session score
        assessment = AssessmentSession.query.get(assessment_id)
        assessment.total_score += selected_score
        assessment.max_score += 3  # Max score per question is always 3

        db.session.commit()

        session["question_index"] = idx + 1
        return redirect(url_for("assessment.take_question"))

    return render_template("assessment/question.html",
                           question=question,
                           options=options,
                           progress=int((idx/len(q_ids))*100))


@assessment_bp.route("/results")
@login_required
def results():
    """Calculate and display final mood/mental health analysis."""
    assessment_id = session.get("assessment_id")
    if not assessment_id:
        return redirect(url_for("assessment.dashboard"))

    assessment = AssessmentSession.query.get(assessment_id)

    # Calculation & Prediction Logic
    percentage = (assessment.total_score / assessment.max_score) * 100 if assessment.max_score > 0 else 0

    if percentage >= 80:
        mood = "Positive / Emotionally Stable"
        insights = "You seem to have a good emotional balance and healthy coping mechanisms."
    elif percentage >= 60:
        mood = "Mild Stress"
        insights = "You're experiencing some emotional pressure. Consider more rest, hobbies, or connecting with friends."
    elif percentage >= 40:
        mood = "Moderate Distress"
        insights = "There are signs of anxiety or emotional fatigue. We suggest mindfulness, journaling, or seeking support."
    else:
        mood = "High Emotional Risk"
        insights = "You may be experiencing significant emotional stress. Please consider speaking with a professional."

    assessment.mood_prediction = mood
    assessment.insights = insights
    db.session.commit()

    # Clear session variables
    session.pop("assessment_id", None)
    session.pop("assessment_questions", None)
    session.pop("question_index", None)

    return render_template("assessment/results.html", assessment=assessment, percentage=percentage)


@assessment_bp.route("/dashboard")
@login_required
def dashboard():
    """Main Mood & Mental Health Analysis tab."""
    user = User.query.get(session["user_id"])

    # Get recent sessions for trend tracking
    history = AssessmentSession.query.filter_by(user_id=user.id).order_by(AssessmentSession.timestamp.desc()).limit(10).all()

    # Calculate weekly trend
    latest = history[0] if history else None

    return render_template("assessment/dashboard.html",
                           user=user,
                           history=history,
                           latest=latest)


def _determine_category(user):
    """Logic to map user profile to question category."""
    if user.age_group == "13–17":
        return "Teenagers"
    if user.age_group == "18–22":
        return "College Students"
    if user.life_stage == "Working Professional":
        return "Working Professionals"
    if user.life_stage == "Trauma-sensitive women":  # Placeholder for specific selection
        return "Trauma-sensitive women"
    return "Adult / General Population"
