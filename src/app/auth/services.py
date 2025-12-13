"""
Authentication services and utilities.
"""

from typing import Optional
from flask import current_app
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from ..models import User, Project, UserSession
from ..extensions import db
from ..utils.image_validator import generate_initial_avatar
from ..services.blob_storage import BlobStorageService


def create_user(email: str, password: str, username: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> Optional[User]:
    """
    Create a new user with the given email, username, and password.

    Args:
        email: User's email address
        password: Plain text password
        username: User's username (max 13 characters, unique)
        first_name: User's first name (optional)
        last_name: User's last name (optional)

    Returns:
        User instance if successful, None if email or username already exists
    """
    if User.query.filter_by(email=email.lower()).first():
        return None

    if User.query.filter_by(username=username.lower()).first():
        return None

    user = User(email=email.lower(), username=username.lower(), first_name=first_name, last_name=last_name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Generate and upload initial avatar
    try:
        avatar_data, content_type = generate_initial_avatar(
            username=username,
            first_name=first_name,
            last_name=last_name
        )

        blob_service = BlobStorageService()
        if blob_service.is_configured():
            avatar_url = blob_service.upload_avatar(user.id, avatar_data, content_type)
            if avatar_url:
                user.avatar_url = avatar_url
                db.session.commit()
                current_app.logger.info(f"Created initial avatar for user: {username} ({email})")
            else:
                current_app.logger.warning(f"Failed to upload initial avatar for user: {username} ({email})")
        else:
            current_app.logger.info(f"Blob storage not configured, skipping initial avatar creation for user: {username} ({email})")
    except Exception as e:
        # Log error but don't fail user creation if avatar generation fails
        current_app.logger.error(f"Error creating initial avatar for user {username} ({email}): {e}", exc_info=True)

    current_app.logger.info(f"Created user: {username} ({email})")
    return user


def authenticate_user(username_or_email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username or email and password.

    Args:
        username_or_email: User's username or email address
        password: Plain text password

    Returns:
        User instance if authentication successful, None otherwise
    """
    # Try username first (case-insensitive)
    user = User.query.filter_by(username=username_or_email.lower()).first()

    # If not found, try email (case-insensitive)
    if not user:
        user = User.query.filter_by(email=username_or_email.lower()).first()

    if user and user.check_password(password) and user.is_active:
        current_app.logger.info(f"User authenticated: {user.username} ({user.email})")
        return user

    return None


def deactivate_user(user_id: str) -> bool:
    """
    Deactivate a user account.

    Args:
        user_id: User's ID

    Returns:
        True if successful, False otherwise
    """
    user = User.query.get(user_id)
    if user:
        user.is_active = False
        db.session.commit()
        current_app.logger.info(f"Deactivated user: {user.email}")
        return True

    return False


def activate_user(user_id: str) -> bool:
    """
    Activate a user account.

    Args:
        user_id: User's ID

    Returns:
        True if successful, False otherwise
    """
    user = User.query.get(user_id)
    if user:
        user.is_active = True
        db.session.commit()
        current_app.logger.info(f"Activated user: {user.email}")
        return True

    return False


def anonymize_user(user_id: str) -> bool:
    """
    Anonymize a user account by removing PII but keeping the record for stats/reports.
    GDPR-compliant alternative to hard deletion.

    Args:
        user_id: User's ID

    Returns:
        True if successful, False otherwise
    """
    try:
        # Prevent self-anonymization
        if hasattr(current_user, 'id') and current_user.id == user_id:
            current_app.logger.warning(f"Attempted self-anonymization blocked for user {user_id}")
            return False

        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User not found for anonymization: {user_id}")
            return False

        # Store original email/username for logging
        original_email = user.email
        original_username = user.username

        # Delete all projects owned by user
        projects = Project.query.filter_by(owner_id=user_id).all()
        project_count = len(projects)
        for project in projects:
            db.session.delete(project)
        if project_count > 0:
            current_app.logger.info(f"Deleted {project_count} project(s) for user {user_id}")

        # Delete all user sessions (contain PII: IP addresses, geolocation, user agent)
        sessions = UserSession.query.filter_by(user_id=user_id).all()
        session_count = len(sessions)
        for session in sessions:
            db.session.delete(session)
        if session_count > 0:
            current_app.logger.info(f"Deleted {session_count} session(s) for user {user_id}")

        # Delete avatar from blob storage
        try:
            blob_service = BlobStorageService()
            if blob_service.is_configured():
                blob_service.delete_user_avatars(user_id)
                current_app.logger.info(f"Deleted avatar for user {user_id}")
        except Exception as e:
            # Don't fail anonymization if avatar deletion fails
            current_app.logger.warning(f"Failed to delete avatar for user {user_id}: {e}")

        # Anonymize user data
        user.is_anonymized = True
        user.email = f"anonymized_{user_id}@deleted.local"
        # Username must be max 13 characters, so use first 8 chars of user_id (UUID)
        # Format: "anon_" + first 8 chars of UUID = 13 chars total
        # Ensure uniqueness by checking if username already exists
        base_username = f"anon_{user_id[:8]}"
        username = base_username
        counter = 1
        while User.query.filter(User.username == username, User.id != user_id).first():
            # If collision, use shorter base and append counter (max 13 chars total)
            suffix = str(counter)
            username = f"anon_{user_id[:8-len(suffix)]}{suffix}"[:13]
            counter += 1
            if counter > 999:  # Safety limit
                # Fallback: use just the first 13 chars of user_id
                username = user_id[:13]
                break
        user.username = username
        user.first_name = None
        user.last_name = None
        user.avatar_url = None
        # Set password to random hash so account can't be accessed
        user.password_hash = generate_password_hash(secrets.token_urlsafe(32))
        user.is_active = False

        db.session.commit()

        current_app.logger.info(f"Anonymized user: {original_email} ({original_username}) -> anonymized_{user_id}")
        return True

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error anonymizing user {user_id}: {e}", exc_info=True)
        return False


def delete_user(user_id: str) -> bool:
    """
    Hard delete a user account and all associated data.
    For GDPR right to erasure requests.

    Args:
        user_id: User's ID

    Returns:
        True if successful, False otherwise
    """
    try:
        # Prevent self-deletion
        if hasattr(current_user, 'id') and current_user.id == user_id:
            current_app.logger.warning(f"Attempted self-deletion blocked for user {user_id}")
            return False

        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User not found for deletion: {user_id}")
            return False

        # Store original email/username for logging
        original_email = user.email
        original_username = user.username

        # Delete all projects owned by user
        projects = Project.query.filter_by(owner_id=user_id).all()
        project_count = len(projects)
        for project in projects:
            db.session.delete(project)
        if project_count > 0:
            current_app.logger.info(f"Deleted {project_count} project(s) for user {user_id}")

        # Delete avatar from blob storage
        try:
            blob_service = BlobStorageService()
            if blob_service.is_configured():
                blob_service.delete_user_avatars(user_id)
                current_app.logger.info(f"Deleted avatar for user {user_id}")
        except Exception as e:
            # Don't fail deletion if avatar deletion fails
            current_app.logger.warning(f"Failed to delete avatar for user {user_id}: {e}")

        # Delete user record
        # Sessions will be automatically deleted via CASCADE (ondelete='CASCADE')
        # Role associations will be automatically deleted via CASCADE
        db.session.delete(user)
        db.session.commit()

        current_app.logger.info(f"Hard deleted user: {original_email} ({original_username})")
        return True

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
        return False
