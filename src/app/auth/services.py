"""
Authentication services and utilities.
"""

from typing import Optional
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import User
from ..extensions import db


def create_user(email: str, password: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> Optional[User]:
    """
    Create a new user with the given email and password.

    Args:
        email: User's email address
        password: Plain text password
        first_name: User's first name (optional)
        last_name: User's last name (optional)

    Returns:
        User instance if successful, None if email already exists
    """
    if User.query.filter_by(email=email.lower()).first():
        return None

    user = User(email=email.lower(), first_name=first_name, last_name=last_name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    current_app.logger.info(f"Created user: {email}")
    return user


def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.

    Args:
        email: User's email address
        password: Plain text password

    Returns:
        User instance if authentication successful, None otherwise
    """
    user = User.query.filter_by(email=email.lower()).first()

    if user and user.check_password(password) and user.is_active:
        current_app.logger.info(f"User authenticated: {email}")
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
