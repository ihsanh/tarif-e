"""
Alışveriş Modelleri
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from .base import Base


class AlisverisListesi(Base):
    """Alışveriş listesi tablosu"""
    __tablename__ = "alisveris_listeleri"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)  # TODO: User tablosu ile ilişkilendir
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    durum = Column(String, default="aktif")  # aktif, tamamlandi
    notlar = Column(String, nullable=True)


class AlisverisUrunu(Base):
    """Alışveriş ürünü tablosu - Listedeki her bir ürün"""
    __tablename__ = "alisveris_urunleri"
    
    id = Column(Integer, primary_key=True, index=True)
    liste_id = Column(Integer)
    malzeme_id = Column(Integer)
    miktar = Column(Float, default=1.0)
    birim = Column(String, default="adet")
    alinma_durumu = Column(Boolean, default=False)
