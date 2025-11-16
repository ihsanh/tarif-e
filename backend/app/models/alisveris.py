"""
Alışveriş Modelleri - Kategori ve Paylaşım Eklendi
backend/app/models/alisveris.py
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import enum


# Enum'ları import et (malzeme.py'den)
from .malzeme import MalzemeKategorisi  # ✅ Relative import


class PaylaşımRolü(str, enum.Enum):
    """Paylaşım yetkileri"""
    GORUNTULEYEBILIR = "view"  # Sadece görüntüle
    DUZENLEYEBILIR = "edit"  # Düzenleyebilir
    SAHIP = "owner"  # Liste sahibi


class AlisverisListesi(Base):
    """Alışveriş listesi"""
    __tablename__ = "alisveris_listesi"
    
    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(200), nullable=False)
    aciklama = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    tamamlandi = Column(Boolean, default=False)
    tamamlanma_tarihi = Column(DateTime, nullable=True)
    
    # İlişkiler
    owner = relationship("User", back_populates="alisveris_listeleri")
    urunler = relationship("AlisverisUrunu", back_populates="liste", cascade="all, delete-orphan")
    paylasilmalar = relationship("ListePaylasim", back_populates="liste", cascade="all, delete-orphan")  # ✅ YENİ


class AlisverisUrunu(Base):
    """Alışveriş listesindeki ürünler"""
    __tablename__ = "alisveris_urunu"
    
    id = Column(Integer, primary_key=True, index=True)
    liste_id = Column(Integer, ForeignKey("alisveris_listesi.id"), nullable=False)
    malzeme_adi = Column(String(100), nullable=False)
    miktar = Column(Float, default=1)
    birim = Column(String(20), default="adet")
    kategori = Column(Enum(MalzemeKategorisi), default=MalzemeKategorisi.DIGER)  # ✅ YENİ
    alinan = Column(Boolean, default=False)
    
    # İlişkiler
    liste = relationship("AlisverisListesi", back_populates="urunler")


class ListePaylasim(Base):
    """Alışveriş listesi paylaşımları"""
    __tablename__ = "liste_paylasim"
    
    id = Column(Integer, primary_key=True, index=True)
    liste_id = Column(Integer, ForeignKey("alisveris_listesi.id"), nullable=False)
    paylasan_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Paylaşan
    paylasilan_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Paylaşılan
    rol = Column(Enum(PaylaşımRolü), default=PaylaşımRolü.GORUNTULEYEBILIR)
    paylasim_tarihi = Column(DateTime, default=datetime.utcnow)
    kabul_edildi = Column(Boolean, default=False)  # Davet kabul edildi mi?
    
    # İlişkiler
    liste = relationship("AlisverisListesi", back_populates="paylasilmalar")
    paylasan = relationship("User", foreign_keys=[paylasan_user_id])
    paylasilan = relationship("User", foreign_keys=[paylasilan_user_id])
