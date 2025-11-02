"""
Veritabanı bağlantısı ve model tanımlamaları
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pathlib import Path

# Config'i import etmeden önce data klasörünü oluştur
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

from .config import settings

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite için gerekli
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Database Models
class User(Base):
    """Kullanıcı modeli"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    ai_mode = Column(String(20), default="auto")  # auto, manual, hybrid, off
    ai_quota = Column(Integer, default=10)
    data_sharing = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    malzemeler = relationship("KullaniciMalzeme", back_populates="user")
    alisveris_listeleri = relationship("AlisverisListesi", back_populates="user")
    fisler = relationship("Fis", back_populates="user")


class Malzeme(Base):
    """Malzeme modeli"""
    __tablename__ = "malzemeler"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    category = Column(String(50))  # sebze, et, baklagil, vb.
    image_url = Column(String(200), nullable=True)
    barcode = Column(String(50), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    kullanici_malzemeleri = relationship("KullaniciMalzeme", back_populates="malzeme")
    tarif_malzemeleri = relationship("TarifMalzeme", back_populates="malzeme")


class KullaniciMalzeme(Base):
    """Kullanıcının elindeki malzemeler"""
    __tablename__ = "kullanici_malzemeleri"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    malzeme_id = Column(Integer, ForeignKey("malzemeler.id"))
    miktar = Column(Float, default=1.0)
    birim = Column(String(20), default="adet")  # kg, gram, adet, vb.
    son_kullanma_tarihi = Column(DateTime, nullable=True)
    eklenme_tarihi = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="malzemeler")
    malzeme = relationship("Malzeme", back_populates="kullanici_malzemeleri")


class Tarif(Base):
    """Tarif modeli"""
    __tablename__ = "tarifler"

    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(200), index=True)
    aciklama = Column(Text)
    talimatlar = Column(Text)  # JSON string olarak adımlar
    sure = Column(Integer)  # dakika cinsinden
    zorluk = Column(String(20))  # kolay, orta, zor
    kategori = Column(String(50))  # ana yemek, çorba, tatlı, vb.
    gorsel_url = Column(String(200), nullable=True)
    begeni_sayisi = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    malzemeler = relationship("TarifMalzeme", back_populates="tarif")


class TarifMalzeme(Base):
    """Tarif-Malzeme ilişkisi"""
    __tablename__ = "tarif_malzemeleri"

    id = Column(Integer, primary_key=True, index=True)
    tarif_id = Column(Integer, ForeignKey("tarifler.id"))
    malzeme_id = Column(Integer, ForeignKey("malzemeler.id"))
    miktar = Column(Float)
    birim = Column(String(20))

    # Relationships
    tarif = relationship("Tarif", back_populates="malzemeler")
    malzeme = relationship("Malzeme", back_populates="tarif_malzemeleri")


class AlisverisListesi(Base):
    """Alışveriş listesi"""
    __tablename__ = "alisveris_listeleri"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    durum = Column(String(20), default="aktif")  # aktif, tamamlandi
    notlar = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="alisveris_listeleri")
    urunler = relationship("AlisverisUrunu", back_populates="liste")


class AlisverisUrunu(Base):
    """Alışveriş listesi ürünleri"""
    __tablename__ = "alisveris_urunleri"

    id = Column(Integer, primary_key=True, index=True)
    liste_id = Column(Integer, ForeignKey("alisveris_listeleri.id"))
    malzeme_id = Column(Integer, ForeignKey("malzemeler.id"))
    miktar = Column(Float)
    birim = Column(String(20))
    alinma_durumu = Column(Boolean, default=False)

    # Relationships
    liste = relationship("AlisverisListesi", back_populates="urunler")


class Fis(Base):
    """Market fişi"""
    __tablename__ = "fisler"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    market_adi = Column(String(100))
    tarih = Column(DateTime)
    toplam_tutar = Column(Float)
    gorsel_url = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="fisler")
    urunler = relationship("FisUrunu", back_populates="fis")


class FisUrunu(Base):
    """Fişteki ürünler"""
    __tablename__ = "fis_urunleri"

    id = Column(Integer, primary_key=True, index=True)
    fis_id = Column(Integer, ForeignKey("fisler.id"))
    urun_adi = Column(String(100))
    miktar = Column(Float)
    birim_fiyat = Column(Float)
    toplam_fiyat = Column(Float)

    # Relationships
    fis = relationship("Fis", back_populates="urunler")


# Database initialization
def init_db():
    """Veritabanını başlat"""
    print(f"📁 Data klasörü: {DATA_DIR}")
    print(f"🗄️  Database URL: {settings.DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Script olarak çalıştırıldığında
if __name__ == "__main__":
    init_db()