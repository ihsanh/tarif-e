"""
Test Fixtures
"""
import sys
from pathlib import Path

# Backend klasörünü Python path'ine ekle
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

print(f"✅ Test backend dir: {backend_dir}")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base


# Test veritabanı (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Her test için temiz bir veritabanı"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Test client - Veritabanı ile"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_malzemeler(db_session):
    """Örnek malzemeler"""
    from app.models import Malzeme, KullaniciMalzeme
    
    malzemeler = [
        {"name": "domates", "miktar": 5, "birim": "adet"},
        {"name": "biber", "miktar": 3, "birim": "adet"},
        {"name": "soğan", "miktar": 2, "birim": "adet"},
    ]
    
    created = []
    for m in malzemeler:
        db_malzeme = Malzeme(name=m["name"], category="sebze")
        db_session.add(db_malzeme)
        db_session.commit()
        db_session.refresh(db_malzeme)
        
        kullanici_malzeme = KullaniciMalzeme(
            user_id=1,
            malzeme_id=db_malzeme.id,
            miktar=m["miktar"],
            birim=m["birim"]
        )
        db_session.add(kullanici_malzeme)
        db_session.commit()
        created.append(kullanici_malzeme)
    
    return created


@pytest.fixture
def sample_tarif():
    """Örnek tarif"""
    return {
        "baslik": "Menemen",
        "aciklama": "Klasik Türk kahvaltısı",
        "malzemeler": [
            "domates - 3 adet",
            "biber - 2 adet",
            "soğan - 1 adet",
            "yumurta - 3 adet"
        ],
        "adimlar": [
            "Soğanı doğrayın",
            "Biberleri ekleyin",
            "Domatesleri ekleyin",
            "Yumurtaları kırın"
        ],
        "sure": 15,
        "zorluk": "kolay"
    }
