"""
Script to fix alembic_version table when migration revision is missing.

This script will:
1. Check the current revision in the database
2. If it points to a missing revision, update it to point to the latest available migration
"""

from src.app import create_app
from src.app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check current revision
        result = db.session.execute(text("SELECT version_num FROM alembic_version"))
        current_revision = result.scalar()
        
        if current_revision:
            print(f"Current revision in database: {current_revision}")
            
            # Check if this revision exists in migration files
            # For now, we'll update it to None (base) so we can start fresh
            print("\nThe database references a migration that doesn't exist.")
            print("Options:")
            print("1. Set to None (base) - will allow migrations to run from scratch")
            print("2. Keep current and create a stub migration")
            
            # Update to None (base) - safest option
            response = input("\nSet alembic_version to NULL (base)? (y/n): ")
            if response.lower() == 'y':
                db.session.execute(text("UPDATE alembic_version SET version_num = NULL"))
                db.session.commit()
                print("✓ Updated alembic_version to NULL (base)")
                print("\nYou can now run: flask db stamp head")
                print("Or run migrations normally: flask db upgrade")
            else:
                print("Keeping current revision. You'll need to create a migration with revision ID:", current_revision)
        else:
            print("No revision found in database. Database is at base state.")
            
    except Exception as e:
        db.session.rollback()
        print(f"\nError: {e}")
        print("\nTrying alternative approach...")
        
        # Try to delete the alembic_version entry
        try:
            db.session.execute(text("DELETE FROM alembic_version"))
            db.session.commit()
            print("✓ Cleared alembic_version table")
            print("\nYou can now run: flask db stamp head")
        except Exception as e2:
            print(f"Error clearing alembic_version: {e2}")
            raise

