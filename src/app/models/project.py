"""
Project model as an example entity.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class Project(db.Model):
    """Project model as an example entity."""
    
    __tablename__ = 'projects'
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Project fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign key to user
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner: Mapped['User'] = relationship('User', back_populates='projects')
    
    def __repr__(self) -> str:
        return f'<Project {self.name}>'
