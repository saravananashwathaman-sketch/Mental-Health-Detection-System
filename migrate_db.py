from app import create_app, db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        columns_to_add = [
            ('age_group', 'VARCHAR(50)'),
            ('life_stage', 'VARCHAR(100)'),
            ('google_id', 'VARCHAR(255)')
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                db.session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"Added column {col_name}")
            except Exception as e:
                db.session.rollback()
                print(f"Column {col_name} might already exist or error: {e}")
        
        print("Database migration attempt finished.")

if __name__ == "__main__":
    migrate()
