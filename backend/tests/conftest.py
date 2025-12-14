"""
Pytest Configuration - Windows SQLite Lock Fix
[FIXED] Database lock issues on Windows
[FIXED] Connection pooling issues
"""
import pytest
import sys
import os
from typing import Generator

# Backend path'i ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db


# Test database - Windows için StaticPool kullan
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_tarif_e.db"

# [CONFIG] Windows için özel konfigürasyon
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # 30 saniye timeout
    },
    poolclass=StaticPool,  # ← ÖNEMLİ: Tek connection pool
    echo=False
)

# SQLite foreign keys aktif et
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=False)
def db_session() -> Generator[Session, None, None]:
    """
    Test database session
    [FIXED] Proper cleanup to avoid locks
    """
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)

    # Session oluştur
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        # [IMPORTANT] Önce session'ı kapat
        session.close()

        # [CLEANUP] Tüm connection'ları kapat
        engine.dispose()

        # [CLEANUP] Tabloları sil
        try:
            Base.metadata.drop_all(bind=engine)
        except Exception as e:
            print(f"[WARN] Drop tables warning: {e}")


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Test client with database override
    """
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
def test_user_data():
    """Test kullanıcı verisi"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "test123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_user(client: TestClient, test_user_data: dict):
    """
    Test kullanıcısı oluştur
    """
    response = client.post("/api/auth/register", json=test_user_data)

    if response.status_code not in [200, 201]:
        print(f"[WARN] Register failed: {response.status_code}")
        print(f"Response: {response.json()}")

    assert response.status_code in [200, 201], f"Registration failed: {response.json()}"

    return test_user_data


@pytest.fixture
def authenticated_client(client: TestClient, test_user_data: dict):
    """
    Authenticated test client
    """
    # Register
    register_response = client.post("/api/auth/register", json=test_user_data)
    assert register_response.status_code in [200, 201]

    # Login
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )

    assert login_response.status_code == 200, f"Login failed: {login_response.json()}"

    token = login_response.json()["access_token"]

    # Add token to headers
    client.headers.update({"Authorization": f"Bearer {token}"})

    return client


@pytest.fixture
def sample_reset_token():
    """Sample reset token for testing"""
    from app.utils.token_generator import generate_reset_token
    return generate_reset_token()


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")


def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    if config.getoption("--runslow"):
        return

    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_sessionstart(session):
    """
    Test session başlarken
    """
    # Test database varsa sil
    test_db_path = "./test_tarif_e.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
            print(f"\n[CLEANUP] Cleaned old test database: {test_db_path}")
        except Exception as e:
            print(f"\n[WARN] Could not remove old test database: {e}")


def pytest_sessionfinish(session, exitstatus):
    """
    Test session bittiğinde
    [FIXED] Proper cleanup
    """
    # [CLEANUP] Engine'i kapat
    engine.dispose()

    # [CLEANUP] Biraz bekle (Windows için)
    import time
    time.sleep(0.5)

    # [CLEANUP] Test database'i sil
    test_db_path = "./test_tarif_e.db"
    if os.path.exists(test_db_path):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                os.remove(test_db_path)
                print(f"\n[SUCCESS] Test database cleaned up: {test_db_path}")
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"\n[WARN] Cleanup attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
                else:
                    print(f"\n[WARN] Could not remove test database after {max_attempts} attempts")
                    print(f"   You may need to manually delete: {test_db_path}")