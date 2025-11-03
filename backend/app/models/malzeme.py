"""
Malzeme Modelleri
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .base import Base


class Malzeme(Base):
    """Malzeme tablosu - Tüm malzemelerin master listesi"""
    __tablename__ = "malzemeler"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, default="genel")


class KullaniciMalzeme(Base):
    """Kullanıcı malzemesi tablosu - Kullanıcının evindeki malzemeler"""
    __tablename__ = "kullanici_malzemeleri"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)  # TODO: User tablosu ile ilişkilendir
    malzeme_id = Column(Integer)
    miktar = Column(Float, default=1.0)
    birim = Column(String, default="adet")
    eklenme_tarihi = Column(DateTime, default=datetime.utcnow)
