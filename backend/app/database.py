"""
Veritabanı Konfigürasyonu
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models import Base
import logging # Logging eklendi

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite için gerekli
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Veritabanı tablolarını oluştur"""
    Base.metadata.create_all(bind=engine)
    # print yerine logger.info
    logger.info("Veritabanı tabloları oluşturuldu")


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()