"""
Pytest Configuration - Debug ile
backend/tests/conftest.py
"""
import os
import sys
from pathlib import Path

# Backend dizinini sys.path'e ekle
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

print("=" * 70)
print("🧪 CONFTEST.PY BAŞLIYOR")
print(f"📁 Working Directory: {os.getcwd()}")
print(f"📁 Backend Directory: {backend_dir}")
print(f"📁 Test File: {__file__}")
print("=" * 70)

# ✅ Test modunu aktif et (database.py import'undan ÖNCE)
os.environ["TESTING"] = "true"
print("✅ TESTING=true set edildi")

import pytest
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, engine as app_engine, SQLALCHEMY_DATABASE_URL, DB_PATH
from app.models import Base

print(f"\n🗄️  DATABASE BİLGİLERİ:")
print(f"   URL: {SQLALCHEMY_DATABASE_URL}")
print(f"   Path: {DB_PATH}")
print(f"   Exists: {DB_PATH.exists()}")
print("=" * 70 + "\n")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Test database'ini hazırla"""
    print("\n🔨 Test database oluşturuluyor...")

    # data/ klasörü yoksa oluştur
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"   📁 Data klasörü: {DB_PATH.parent}")

    # Tabloları oluştur
    Base.metadata.create_all(bind=app_engine)
    print(f"   ✅ Tablolar oluşturuldu: {DB_PATH}")

    yield

    # Test bittikten sonra temizle (opsiyonel)
    print(f"\n🧹 Test database temizleniyor: {DB_PATH}")
    # Base.metadata.drop_all(bind=app_engine)


@pytest.fixture(scope="function")
def db_session():
    """Her test için temiz bir session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=app_engine
    )

    connection = app_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Test client with test database"""
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
    """Test için örnek malzemeler"""
    from app.models import Malzeme, MalzemeKategorisi, User

    # Test kullanıcısı oluştur
    test_user = User(
        email="conftest_sample@example.com",
        username="conftest_sample_user",
        hashed_password="test123",
        full_name="Conftest Sample User"
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    # Malzemeleri ekle
    malzemeler = [
        Malzeme(
            name="sample_domates",
            miktar=10,
            birim="adet",
            kategori=MalzemeKategorisi.MEYVE_SEBZE,
            user_id=test_user.id
        ),
        Malzeme(
            name="sample_süt",
            miktar=2,
            birim="litre",
            kategori=MalzemeKategorisi.SUT_URUNLERI,
            user_id=test_user.id
        ),
        Malzeme(
            name="sample_ekmek",
            miktar=1,
            birim="adet",
            kategori=MalzemeKategorisi.TAHIL_BAKLAGIL,
            user_id=test_user.id
        ),
    ]

    for malzeme in malzemeler:
        db_session.add(malzeme)

    db_session.commit()

    return malzemeler
