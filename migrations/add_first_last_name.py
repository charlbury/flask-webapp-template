"""
Migration script to add first_name and last_name columns to users table.

Run this script after updating the User model:
    python migrations/add_first_last_name.py
"""

from src.app import create_app
from src.app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        # Get database dialect to use correct SQL syntax
        dialect = db.engine.dialect.name
        
        if 'first_name' not in columns:
            print("Adding first_name column...")
            if dialect == 'mssql':
                # SQL Server syntax
                db.session.execute(text("ALTER TABLE users ADD first_name NVARCHAR(100) NULL"))
            else:
                # SQLite/PostgreSQL syntax
                db.session.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100)"))
            print("✓ Added first_name column")
        else:
            print("✓ first_name column already exists")
        
        if 'last_name' not in columns:
            print("Adding last_name column...")
            if dialect == 'mssql':
                # SQL Server syntax
                db.session.execute(text("ALTER TABLE users ADD last_name NVARCHAR(100) NULL"))
            else:
                # SQLite/PostgreSQL syntax
                db.session.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100)"))
            print("✓ Added last_name column")
        else:
            print("✓ last_name column already exists")
        
        db.session.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"\nError during migration: {e}")
        raise

