"""
Database Configuration - Absolute Path ile
backend/app/database.py
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Backend dizinini bul (app/ klasörünün parent'ı)
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"

# data/ klasörü yoksa oluştur
DATA_DIR.mkdir(exist_ok=True)

# Test modunda mı kontrol et
TESTING = os.getenv("TESTING", "false").lower() == "true"

if TESTING:
    # Test için ayrı database - ABSOLUTE PATH
    DB_PATH = DATA_DIR / "test_tarif_e.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
    print(f"⚠️  TEST DATABASE kullanılıyor: {DB_PATH}")
else:
    # Production database - ABSOLUTE PATH
    DB_PATH = DATA_DIR / "tarif_e.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
    print(f"✅ PRODUCTION DATABASE kullanılıyor: {DB_PATH}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
