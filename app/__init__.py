"""
app/__init__.py — Flask application factory.

Creates and configures the Flask app, registers all blueprints,
and initialises the SQLAlchemy database.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from app.config import Config

# Shared instances
db = SQLAlchemy()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Initialise extensions ────────────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)

    # ── Google OAuth via Flask-Dance ─────────────────────────────────────────
    from flask_dance.contrib.google import make_google_blueprint
    google_bp = make_google_blueprint(
        client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
               "https://www.googleapis.com/auth/userinfo.profile"],
        redirect_to="auth.google_authorized",
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    # ── Register app blueprints ──────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.chat import chat_bp
    from app.routes.mood import mood_bp
    from app.routes.privacy import privacy_bp
    from app.routes.ai_chat import ai_chat_bp
    from app.routes.ml_insights import ml_insights_bp
    from app.routes.media import media_bp
    from app.routes.assessment import assessment_bp
    from app.routes.personalized_assessment import personalized_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(mood_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(ai_chat_bp)
    app.register_blueprint(ml_insights_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(personalized_bp)

    # ── Inject helpline context into every template ──────────────────────────
    from app.helplines import (
        PRIMARY_NAME, PRIMARY_NUMBER,
        SECONDARY_NAME, SECONDARY_NUMBER,
        HELPLINES,
    )

    @app.context_processor
    def inject_helplines():
        return dict(
            primary_helpline_name=PRIMARY_NAME,
            primary_helpline_number=PRIMARY_NUMBER,
            secondary_helpline_name=SECONDARY_NAME,
            secondary_helpline_number=SECONDARY_NUMBER,
            helplines=HELPLINES,
        )

    # ── Create DB tables (if they don't exist) ───────────────────────────────
    with app.app_context():
        db.create_all()

    return app
