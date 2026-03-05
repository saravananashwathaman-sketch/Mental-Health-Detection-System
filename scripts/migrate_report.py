from app import create_app, db
import sqlite3
import os

def migrate():
    app = create_app()
    with app.app_context():
        # Get database path
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            # For relative paths, prepend instance or root if needed, but here let's assume absolute or current
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("ALTER TABLE mental_health_reports ADD COLUMN color_name VARCHAR(50)")
                print("Added color_name column.")
            except sqlite3.OperationalError:
                print("color_name column already exists.")
                
            try:
                cursor.execute("ALTER TABLE mental_health_reports ADD COLUMN color_hex VARCHAR(20)")
                print("Added color_hex column.")
            except sqlite3.OperationalError:
                print("color_hex column already exists.")
            
            conn.commit()
            conn.close()
            print("Migration complete.")
        else:
            print("Not a SQLite database.")

if __name__ == "__main__":
    migrate()
