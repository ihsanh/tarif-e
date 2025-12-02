"""
User Profile Model - Kullanıcı profil ayarları
backend/app/models/user_profile.py
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserProfile(Base):
    """Kullanıcı profil ayarları"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Profil bilgileri
    bio = Column(Text, nullable=True)  # Kısa biyografi
    profile_photo_url = Column(String(500), nullable=True)  # Profil fotoğrafı URL
    
    # Diyet tercihleri (JSON array olarak saklanır)
    # Örnek: ["vegan", "glutensiz"]
    dietary_preferences = Column(JSON, default=list)
    
    # Alerji bilgileri (JSON array olarak saklanır)
    # Örnek: ["fıstık", "süt", "yumurta"]
    allergies = Column(JSON, default=list)
    
    # Sevmediği yiyecekler
    dislikes = Column(JSON, default=list)
    
    # Tema tercihi
    theme = Column(String(50), default="light")  # "light", "dark", "auto"
    
    # Dil tercihi
    language = Column(String(10), default="tr")  # "tr", "en"
    
    # Tarih damgaları
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, theme={self.theme})>"
