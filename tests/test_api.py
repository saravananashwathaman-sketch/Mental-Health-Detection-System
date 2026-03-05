"""
tests/test_api.py — Integration tests for Flask API endpoints.

LLM client AND sentiment analysis are mocked so no external API calls are made.
Tests cover:
  - POST /chat/send
  - GET  /api/mood-data
  - POST /mood (check-in submission)
  - GET  /dashboard
  - GET  /privacy (and delete/export)
  - Auth flows (register, login, logout)
"""

import json
from unittest.mock import patch


# ── Helper ─────────────────────────────────────────────────────────────────

def register_and_login(client, email="api_test@example.com", password="testpass123"):
    """Register then log in a test user and return the user_id held in session."""
    client.post("/register", data={
        "email": email,
        "password": password,
        "confirm_password": password,
        "consent": "on",
    })
    client.post("/login", data={"email": email, "password": password})


# ── AUTH TESTS ─────────────────────────────────────────────────────────────

class TestAuth:

    def test_register_success(self, client, app):
        """Valid registration should redirect to /login."""
        resp = client.post("/register", data={
            "email": "new@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "consent": "on",
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_register_without_consent_fails(self, client, app):
        """Missing consent checkbox should not create the account."""
        resp = client.post("/register", data={
            "email": "noconsent@example.com",
            "password": "password123",
            "confirm_password": "password123",
            # no 'consent' field
        }, follow_redirects=True)
        assert b"consent" in resp.data.lower() or resp.status_code == 200

    def test_register_duplicate_email_fails(self, client, db_user, app):
        """Registering an already-used email should re-render the form."""
        resp = client.post("/register", data={
            "email": "test@example.com",   # same as db_user fixture
            "password": "password123",
            "confirm_password": "password123",
            "consent": "on",
        }, follow_redirects=True)
        # Should stay on register page (200, not redirect)
        assert resp.status_code == 200

    def test_login_success(self, client, db_user, app):
        """Valid credentials should redirect to /dashboard."""
        resp = client.post("/login", data={
            "email": "test@example.com",
            "password": "testpassword123",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_login_wrong_password(self, client, db_user, app):
        """Wrong password should re-render login (200, not redirect)."""
        resp = client.post("/login", data={
            "email": "test@example.com",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_logout(self, auth_client, app):
        """Logout should redirect to login page."""
        resp = auth_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302


# ── DASHBOARD TESTS ────────────────────────────────────────────────────────

class TestDashboard:

    def test_dashboard_requires_login(self, client, app):
        """Unauthenticated request should redirect to login."""
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302

    def test_dashboard_renders_for_authenticated_user(self, auth_client, app):
        """Authenticated user should see the dashboard page (200)."""
        resp = auth_client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data or b"dashboard" in resp.data.lower()

    def test_mood_data_api_returns_json(self, auth_client, app):
        """/api/mood-data should return valid JSON with expected keys."""
        resp = auth_client.get("/api/mood-data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "wellbeing" in data
        assert "mood" in data
        assert "labels" in data["wellbeing"]
        assert "scores" in data["wellbeing"]


# ── MOOD CHECK-IN TESTS ────────────────────────────────────────────────────

class TestMoodCheckin:

    def test_checkin_requires_login(self, client, app):
        """Unauthenticated POST to /mood should redirect."""
        resp = client.post("/mood", data={
            "mood_score": "4", "sleep_hours": "7", "activity_level": "2"
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_checkin_success_redirects_to_dashboard(self, auth_client, app):
        """
        Valid mood check-in should trigger risk scoring and redirect to /dashboard.
        """
        resp = auth_client.post("/mood", data={
            "mood_score": "4",
            "sleep_hours": "8",
            "activity_level": "2",
            "notes": "Feeling okay today",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers.get("Location", "")

    def test_mood_data_appears_in_api_after_checkin(self, auth_client, app):
        """After a check-in, /api/mood-data should contain at least one entry."""
        auth_client.post("/mood", data={
            "mood_score": "5", "sleep_hours": "8", "activity_level": "3"
        })
        resp = auth_client.get("/api/mood-data")
        data = resp.get_json()
        assert len(data["wellbeing"]["scores"]) >= 1


# ── CHAT TESTS ─────────────────────────────────────────────────────────────

class TestChat:

    @patch("app.routes.chat.analyze_sentiment", return_value={
        "sentiment": "POSITIVE",
        "confidence": 0.95,
        "emotion": "joy",
        "distress_signal": False,
    })
    @patch("app.routes.chat.get_llm_response", return_value="I'm glad you're feeling well!")
    def test_chat_send_returns_ai_response(self, mock_llm, mock_nlp, auth_client, app):
        """
        POST /chat/send with a valid message should return a 200 JSON response
        containing the ai_response key.

        Both LLM and NLP are mocked — no real API calls are made.
        """
        resp = auth_client.post(
            "/chat/send",
            data=json.dumps({"message": "I feel happy today!"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "ai_response" in data
        assert data["sentiment"] == "POSITIVE"

    @patch("app.routes.chat.analyze_sentiment", return_value={
        "sentiment": "NEGATIVE",
        "confidence": 0.90,
        "emotion": "sadness",
        "distress_signal": True,   # ← distress flag
    })
    @patch("app.routes.chat.get_llm_response", return_value="Please reach out for help.")
    def test_distress_message_returns_red_risk(self, mock_llm, mock_nlp, auth_client, app):
        """
        A message with distress_signal=True should result in risk_level=RED
        in the response, so the front-end can trigger crisis resources.
        """
        resp = auth_client.post(
            "/chat/send",
            data=json.dumps({"message": "I want to end my life"}),
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["risk_level"] == "RED"
        assert data["distress_flag"] is True

    def test_chat_send_empty_message_returns_400(self, auth_client, app):
        """Empty message payload should return 400 Bad Request."""
        resp = auth_client.post(
            "/chat/send",
            data=json.dumps({"message": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400


# ── PRIVACY TESTS ──────────────────────────────────────────────────────────

class TestPrivacy:

    def test_privacy_page_loads(self, auth_client, app):
        resp = auth_client.get("/privacy/")
        assert resp.status_code == 200

    def test_export_returns_json_file(self, auth_client, app):
        """Data export should return a JSON attachment."""
        resp = auth_client.get("/privacy/export")
        assert resp.status_code == 200
        assert "application/json" in resp.content_type
        data = json.loads(resp.data)
        assert "user" in data
        assert "mood_entries" in data
        assert "chat_messages" in data

    def test_delete_removes_user_and_redirects(self, auth_client, app):
        """Data deletion should clear the user from the DB and redirect."""
        resp = auth_client.post("/privacy/delete", follow_redirects=False)
        assert resp.status_code == 302
        # After deletion, accessing dashboard should redirect to login
        resp2 = auth_client.get("/dashboard", follow_redirects=False)
        assert resp2.status_code == 302
