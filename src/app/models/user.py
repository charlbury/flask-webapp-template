"""
User model with authentication and role management.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class User(UserMixin, db.Model):
    """User model with authentication and role management."""

    __tablename__ = 'users'

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(13), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Profile fields
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    roles: Mapped[List['Role']] = relationship(
        'Role',
        secondary='user_roles',
        back_populates='users',
        lazy='select'
    )
    projects: Mapped[List['Project']] = relationship('Project', back_populates='owner', lazy='dynamic')
    sessions: Mapped[List['UserSession']] = relationship('UserSession', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Set password hash using PBKDF2."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def add_role(self, role_name: str) -> bool:
        """Add a role to the user."""
        from .role import Role

        role = Role.query.filter_by(name=role_name).first()
        if role and role not in self.roles:
            self.roles.append(role)
            return True
        return False

    def remove_role(self, role_name: str) -> bool:
        """Remove a role from the user."""
        from .role import Role
        role = Role.query.filter_by(name=role_name).first()
        if role and role in self.roles:
            self.roles.remove(role)
            return True
        return False

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.has_role('admin')

    def get_avatar_url(self) -> str:
        """Get avatar URL or return default avatar."""
        from flask import url_for
        if self.avatar_url:
            return self.avatar_url
        return url_for('static', filename='admin/img/bruce-mars.jpg')

    def __repr__(self) -> str:
        return f'<User {self.username} ({self.email})>'
