"""
Authentication services and utilities.
"""

from typing import Optional
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import User
from ..extensions import db


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
    
    if User.query.filter_by(username=username).first():
        return None

    user = User(email=email.lower(), username=username, first_name=first_name, last_name=last_name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

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
    # Try username first (case-sensitive)
    user = User.query.filter_by(username=username_or_email).first()
    
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
