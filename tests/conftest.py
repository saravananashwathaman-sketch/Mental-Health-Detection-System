"""
tests/conftest.py — pytest fixtures for the mental health app test suite.

Provides:
  - app      : Flask app configured for testing (in-memory SQLite)
  - client   : Flask test client (no real HTTP)
  - db_user  : A seeded test user already in the database
  - auth_client : Test client with a pre-authenticated session

All fixtures use function scope so each test gets a fresh database.
"""

import pytest
from app import create_app, db as _db
from app.models import User
from app.config import TestingConfig


@pytest.fixture(scope="function")
def app():
    """
    Create a Flask application instance configured for testing.
    Uses an in-memory SQLite database that is dropped after each test.
    """
    flask_app = create_app(TestingConfig)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Direct access to the SQLAlchemy db object within an app context."""
    with app.app_context():
        yield _db


@pytest.fixture(scope="function")
def db_user(app):
    """Seed a test user in the database and return the User instance."""
    with app.app_context():
        user = User(email="test@example.com", consent_given=True)
        user.set_password("testpassword123")
        _db.session.add(user)
        _db.session.commit()
        # Re-query to attach to the current session
        return _db.session.get(User, user.id)


@pytest.fixture(scope="function")
def auth_client(client, db_user, app):
    """
    Test client with a pre-authenticated session.
    Avoids having to POST /login in every test that needs auth.
    """
    with app.app_context():
        user = _db.session.merge(db_user)
        with client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["user_email"] = user.email
    return client
