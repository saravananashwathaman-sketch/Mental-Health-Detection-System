from app import create_app, db
from sqlalchemy import text
import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def fix_db():
    app = create_app()
    with app.app_context():
        # 1. Create any missing tables (ImagePool, ImageTestSession)
        db.create_all()
        print("Created new tables (if any).")

        # 2. Add session_id to image_emotion_tests
        try:
            db.session.execute(text("ALTER TABLE image_emotion_tests ADD COLUMN session_id INTEGER REFERENCES image_test_sessions(id)"))
            db.session.commit()
            print("Added session_id column to image_emotion_tests.")
        except Exception as e:
            db.session.rollback()
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("session_id column already exists.")
            else:
                print(f"Error adding session_id: {e}")

        # 3. Ensure image_pool is seeded (safety check)
        from scripts.seed_image_pool import seed_image_pool
        seed_image_pool()
        print("Initialization complete.")

if __name__ == "__main__":
    fix_db()
