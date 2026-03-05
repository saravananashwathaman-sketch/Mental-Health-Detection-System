"""
app/routes/auth.py — Authentication blueprint.

Routes:
  GET  /              → redirect to dashboard or login
  GET  /register      → registration form
  POST /register      → create user account (requires consent)
  GET  /login         → login form
  POST /login         → verify credentials and create session
  GET  /logout        → destroy session
  GET  /login/google/authorized → Google OAuth callback
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash
)
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """
    Decorator that redirects unauthenticated users to the login page.
    Usage: @login_required above a route function.
    """
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


@auth_bp.route("/")
def index():
    """Root URL — show landing page if not logged in, else dashboard."""
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    GET  -> render registration form.
    POST -> validate inputs, require consent, create user, redirect to login.
    """
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        consent = request.form.get("consent")   # checkbox value "on" or None

        errors = []
        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if not consent:
            errors.append(
                "You must give consent to data processing to use this service."
            )

        if not errors and User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html", email=email)

        user = User(email=email, consent_given=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  -> render login form.
    POST -> verify credentials, create session, redirect to dashboard.
    """
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_email"] = user.email
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard.index"))

        flash("Invalid email or password. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    """Clear the session and redirect to the login page."""
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for("auth.login"))


# ── Google OAuth Callback ────────────────────────────────────────────────────

@auth_bp.route("/auth/google/callback")
def google_authorized():
    """
    Callback URL that Google redirects to after the user approves OAuth.
    Flask-Dance's google blueprint fetches the token; we just read the profile.
    """
    from flask_dance.contrib.google import google as google_oauth

    if not google_oauth.authorized:
        flash("Google login failed or was cancelled. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    try:
        resp = google_oauth.get("/oauth2/v2/userinfo")
        if not resp.ok:
            raise ValueError(f"Google API error: {resp.text}")
        info = resp.json()
    except Exception as exc:
        flash(f"Could not fetch your Google profile: {exc}", "danger")
        return redirect(url_for("auth.login"))

    email = info.get("email", "").strip().lower()
    if not email:
        flash("Google did not return an email address. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    # Find or create user - OAuth users get consent auto-granted
    user = User.query.filter_by(email=email).first()
    if not user:
        import secrets
        user = User(email=email, consent_given=True)
        user.set_password(secrets.token_hex(32))
        db.session.add(user)
        db.session.commit()
        flash("Account created via Google! Welcome to MindGuard.", "success")
    else:
        flash("Welcome back! Signed in with Google.", "success")

    session["user_id"] = user.id
    session["user_email"] = user.email
    return redirect(url_for("dashboard.index"))
