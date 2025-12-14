"""
User Model - Authentication
backend/app/models/user.py
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timedelta


class User(Base):
    """Kullanıcı modeli"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    # ============================================
    # RELATIONSHIPS
    # ============================================

    # Malzeme relationship
    malzemeler = relationship(
        "Malzeme",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    # Alışveriş Listeleri relationship
    alisveris_listeleri = relationship(
        "AlisverisListesi",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    # ✅ User Profile relationship
    # SADECE BİR TANE OLMALI - DUPLICATE KALDIRILDI
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # ✅ Favori Tarifler relationship
    favoriler = relationship(
        "FavoriTarif",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    menu_plans = relationship("WeeklyMenuPlan", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

    def set_reset_token(self, token: str, expires_minutes: int = 30):
        """Reset token ayarla"""
        self.reset_token = token
        self.reset_token_expires = datetime.utcnow() + timedelta(minutes=expires_minutes)

    def clear_reset_token(self):
        """Reset token'ı temizle"""
        self.reset_token = None
        self.reset_token_expires = None

    def is_reset_token_valid(self, token: str) -> bool:
        """Reset token geçerli mi kontrol et"""
        if not self.reset_token or not self.reset_token_expires:
            return False

        if self.reset_token != token:
            return False

        if datetime.utcnow() > self.reset_token_expires:
            return False

        return True