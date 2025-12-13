"""
UserSession model for tracking user login sessions.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class UserSession(db.Model):
    """User session model for tracking login sessions with device and location details."""

    __tablename__ = 'user_sessions'

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key to User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Session identification
    session_token: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Network information
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 can be up to 45 chars

    # User agent information
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)  # Raw user agent string
    browser_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    browser_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    os_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # desktop, mobile, tablet

    # Geolocation information
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # e.g., "EU", "US"
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ISO country code

    # Timestamps
    login_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='sessions')

    # Indexes
    __table_args__ = (
        Index('ix_user_sessions_user_id_last_activity', 'user_id', 'last_activity_at'),
    )

    def is_expired(self) -> bool:
        """Check if session has expired (24 hours of inactivity)."""
        if not self.is_active:
            return True
        expiration_time = self.last_activity_at + timedelta(hours=24)
        return datetime.utcnow() > expiration_time

    def should_be_cleaned_up(self) -> bool:
        """Check if session should be cleaned up (90 days old)."""
        cleanup_time = self.login_at + timedelta(days=90)
        return datetime.utcnow() > cleanup_time

    def __repr__(self) -> str:
        return f'<UserSession {self.session_token[:8]}... ({self.user_id})>'

