"""
Tarif Modelleri
backend/app/models/tarif.py
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class FavoriTarif(Base):
    """Favori tarifler tablosu"""
    __tablename__ = "favoriler"  # ✅ DÜZELTİLDİ: "favori_tarifler" yerine "favoriler"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Tarif bilgileri
    baslik = Column(String(200), nullable=False)
    aciklama = Column(Text, nullable=True)
    malzemeler = Column(Text, nullable=False)  # JSON string
    adimlar = Column(Text, nullable=False)  # JSON string

    # Ek bilgiler
    sure = Column(String(50), nullable=True)  # ✅ String olarak (eski: Integer)
    zorluk = Column(String(20), nullable=True)
    kategori = Column(String(50), nullable=True)

    # Metadata
    eklenme_tarihi = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ============================================
    # RELATIONSHIP
    # ============================================

    # User ile ilişki
    user = relationship("User", back_populates="favoriler")

    def __repr__(self):
        return f"<FavoriTarif(id={self.id}, baslik='{self.baslik}', user_id={self.user_id})>"