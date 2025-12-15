"""
Subscription Model - User subscription management
backend/app/models/subscription.py
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timedelta


class Subscription(Base):
    """Kullanıcı abonelik modeli"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    tier = Column(String(50), default="pro", nullable=False)  # "standard" or "pro"
    billing_cycle = Column(String(50), default="monthly", nullable=False)  # "monthly" or "yearly"
    status = Column(String(50), default="active", nullable=False)  # "active", "expired", "cancelled"
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier={self.tier}, status={self.status})>"

    def calculate_end_date(self):
        """Billing cycle'a göre bitiş tarihini hesapla"""
        if not self.start_date:
            self.start_date = datetime.utcnow()

        if self.billing_cycle == "monthly":
            # 1 ay ekle
            self.end_date = self.start_date + timedelta(days=30)
        elif self.billing_cycle == "yearly":
            # 1 yıl ekle
            self.end_date = self.start_date + timedelta(days=365)
        else:
            # Varsayılan: 1 ay
            self.end_date = self.start_date + timedelta(days=30)

    def is_active(self) -> bool:
        """Abonelik aktif mi kontrol et"""
        if self.status != "active":
            return False

        if self.end_date and datetime.utcnow() > self.end_date:
            return False

        return True

    def renew(self):
        """Aboneliği yenile"""
        if self.auto_renew:
            self.start_date = datetime.utcnow()
            self.calculate_end_date()
            self.status = "active"
