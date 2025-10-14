"""
Role model for RBAC system.
"""

import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, func, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    db.Model.metadata,
    Column('user_id', String(36), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)


class Role(db.Model):
    """Role model for RBAC system."""
    
    __tablename__ = 'roles'
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Role fields
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    users: Mapped[List['User']] = relationship(
        'User',
        secondary=user_roles,
        back_populates='roles',
        lazy='dynamic'
    )
    
    def __repr__(self) -> str:
        return f'<Role {self.name}>'
