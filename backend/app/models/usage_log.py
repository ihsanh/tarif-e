"""
UsageLog Model - Track user actions and usage
backend/app/models/usage_log.py
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class UsageLog(Base):
    """Kullanıcı kullanım kayıtları modeli"""
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)  # "recipe_suggestion", etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")

    def __repr__(self):
        return f"<UsageLog(id={self.id}, user_id={self.user_id}, action={self.action_type}, created_at={self.created_at})>"
