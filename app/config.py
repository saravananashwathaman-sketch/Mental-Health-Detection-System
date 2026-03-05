"""
app/config.py — Application configuration.
Reads settings from environment variables / .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

    # Database — SQLite by default, no setup required
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///mental_health.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM settings
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")  # "groq" or "gemini"
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    # Groq model name — llama-3.1-8b-instant replaces decommissioned llama3-8b-8192
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    # Gemini model name
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")


class TestingConfig(Config):
    """Configuration for pytest — uses in-memory SQLite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
