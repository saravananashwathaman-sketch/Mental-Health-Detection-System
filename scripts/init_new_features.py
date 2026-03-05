from app import create_app, db
import os

def init_db():
    app = create_app()
    with app.app_context():
        # This will create all tables that don't exist yet
        db.create_all()
        print("Database tables for new features initialized successfully.")

if __name__ == "__main__":
    init_db()
