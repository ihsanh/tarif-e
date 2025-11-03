"""
Tarif Modelleri
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .base import Base


class FavoriTarif(Base):
    """Favori tarifler tablosu"""
    __tablename__ = "favori_tarifler"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)  # TODO: User tablosu ile ilişkilendir
    baslik = Column(String, nullable=False)
    aciklama = Column(Text, nullable=True)
    malzemeler = Column(Text, nullable=False)  # JSON string
    adimlar = Column(Text, nullable=False)  # JSON string
    sure = Column(Integer, nullable=True)
    zorluk = Column(String, nullable=True)
    kategori = Column(String, nullable=True)
    eklenme_tarihi = Column(DateTime, default=datetime.utcnow)
