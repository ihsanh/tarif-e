"""
Malzeme Model - Kategori Eklendi
backend/app/models/malzeme.py
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import enum


class MalzemeKategorisi(str, enum.Enum):
    """Malzeme kategorileri"""
    MEYVE_SEBZE = "meyve_sebze"
    ET_TAVUK_BALIK = "et_tavuk_balik"
    SUT_URUNLERI = "süt_ürünleri"
    TAHIL_BAKLAGIL = "tahıl_baklagil"
    SARKUTERI = "şarküteri"
    DONUK_GIDA = "donuk_gıda"
    ATISTIRMALIK = "atıştırmalık"
    ICECEK = "içecek"
    TEMIZLIK = "temizlik"
    KISISEL_BAKIM = "kişisel_bakım"
    DIGER = "diğer"


class Malzeme(Base):
    """Kullanıcının malzeme dolabı"""
    __tablename__ = "malzeme"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    miktar = Column(Float, default=0)
    birim = Column(String(20), default="adet")
    kategori = Column(Enum(MalzemeKategorisi), default=MalzemeKategorisi.DIGER)  # ✅ YENİ
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    eklenme_tarihi = Column(DateTime, default=datetime.utcnow)
    son_guncelleme = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    owner = relationship("User", back_populates="malzemeler")


class KullaniciMalzeme(Base):
    """
    Kullanıcının malzeme dolabı (alternatif tablo)
    Not: Malzeme tablosu ile aynı - geriye dönük uyumluluk için
    """
    __tablename__ = "kullanici_malzeme"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    miktar = Column(Float, default=0)
    birim = Column(String(20), default="adet")
    kategori = Column(Enum(MalzemeKategorisi), default=MalzemeKategorisi.DIGER)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    eklenme_tarihi = Column(DateTime, default=datetime.utcnow)
    son_guncelleme = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    owner = relationship("User", foreign_keys=[user_id])
