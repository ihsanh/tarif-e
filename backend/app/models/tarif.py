"""
Tarif Modelleri
backend/app/models/tarif.py
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class FavoriTarif(Base):
    """Favori tarifler tablosu"""
    __tablename__ = "favori_tarifler"

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

    user = relationship("User", back_populates="favoriler")
    menu_items = relationship("MenuItem", back_populates="tarif")


    def __repr__(self):
        return f"<FavoriTarif(id={self.id}, baslik='{self.baslik}', user_id={self.user_id})>"