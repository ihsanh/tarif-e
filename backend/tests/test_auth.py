"""
Authentication Tests - Login, Register, Token testleri
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)


# Test veritabanını sıfırla
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestRegister:
    """Kullanıcı kayıt testleri"""
    
    def test_register_basarili(self):
        """Başarılı kayıt"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["user"]["username"] == "testuser"
        assert result["user"]["email"] == "test@example.com"
    
    def test_register_duplicate_email(self):
        """Aynı email ile ikinci kayıt - hata vermeli"""
        data = {
            "email": "test@example.com",
            "username": "testuser1",
            "password": "test123"
        }
        # İlk kayıt
        client.post("/api/auth/register", json=data)
        
        # İkinci kayıt - farklı username ama aynı email
        data2 = {
            "email": "test@example.com",  # Aynı email
            "username": "testuser2",
            "password": "test123"
        }
        response = client.post("/api/auth/register", json=data2)
        
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()
    
    def test_register_duplicate_username(self):
        """Aynı username ile ikinci kayıt - hata vermeli"""
        data = {
            "email": "test1@example.com",
            "username": "testuser",
            "password": "test123"
        }
        # İlk kayıt
        client.post("/api/auth/register", json=data)
        
        # İkinci kayıt - farklı email ama aynı username
        data2 = {
            "email": "test2@example.com",
            "username": "testuser",  # Aynı username
            "password": "test123"
        }
        response = client.post("/api/auth/register", json=data2)
        
        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self):
        """Geçersiz email formatı"""
        data = {
            "email": "invalid-email",  # @ yok
            "username": "testuser",
            "password": "test123"
        }
        response = client.post("/api/auth/register", json=data)
        
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self):
        """Kısa şifre - min 6 karakter"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123"  # 3 karakter
        }
        response = client.post("/api/auth/register", json=data)
        
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Login testleri"""
    
    def test_login_basarili_email(self):
        """Email ile başarılı login"""
        # Önce kayıt ol
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123"
        }
        client.post("/api/auth/register", json=register_data)
        
        # Login yap - EMAIL ile
        login_data = {
            "username": "test@example.com",  # Email kullanılabilir
            "password": "test123"
        }
        response = client.post("/api/auth/login", data=login_data)  # data= not json=
        
        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert result["user"]["email"] == "test@example.com"
    
    def test_login_basarili_username(self):
        """Username ile başarılı login"""
        # Önce kayıt ol
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123"
        }
        client.post("/api/auth/register", json=register_data)
        
        # Login yap - USERNAME ile
        login_data = {
            "username": "testuser",
            "password": "test123"
        }
        response = client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert result["user"]["username"] == "testuser"
    
    def test_login_yanlis_sifre(self):
        """Yanlış şifre ile login"""
        # Önce kayıt ol
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123"
        }
        client.post("/api/auth/register", json=register_data)
        
        # Yanlış şifre ile login
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "şifre" in response.json()["detail"].lower()
    
    def test_login_olmayan_kullanici(self):
        """Olmayan kullanıcı ile login"""
        login_data = {
            "username": "nonexistent",
            "password": "test123"
        }
        response = client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "kullanıcı" in response.json()["detail"].lower()


class TestTokenValidation:
    """Token doğrulama testleri"""
    
    def test_gecerli_token_ile_api_erisim(self):
        """Geçerli token ile API erişimi"""
        # Kayıt ol ve token al
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123"
        }
        register_response = client.post("/api/auth/register", json=register_data)
        token = register_response.json()["access_token"]
        
        # Token ile malzeme listesine eriş
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/malzeme/liste", headers=headers)
        
        assert response.status_code == 200
    
    def test_gecersiz_token_ile_api_erisim(self):
        """Geçersiz token ile API erişimi - 401 dönmeli"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/malzeme/liste", headers=headers)
        
        assert response.status_code == 401
    
    def test_token_olmadan_api_erisim(self):
        """Token olmadan API erişimi - 401 dönmeli"""
        response = client.get("/api/malzeme/liste")
        
        assert response.status_code == 401


class TestUserProfile:
    """Kullanıcı profil testleri"""
    
    def test_me_endpoint(self):
        """Mevcut kullanıcı bilgisi"""
        # Kayıt ol
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123",
            "full_name": "Test User"
        }
        register_response = client.post("/api/auth/register", json=register_data)
        token = register_response.json()["access_token"]
        
        # Profil bilgisi al
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        user = response.json()
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert user["full_name"] == "Test User"
    
    def test_me_endpoint_without_token(self):
        """Token olmadan profil bilgisi - 401"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401


class TestLogout:
    """Logout testleri"""
    
    def test_logout_basarili(self):
        """Başarılı logout"""
        # Kayıt ol
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123"
        }
        register_response = client.post("/api/auth/register", json=register_data)
        token = register_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/logout", headers=headers)
        
        # Not: Şu anda logout backend'de token'ı invalidate etmiyor
        # Sadece 200 OK dönüyor. Frontend localStorage'ı temizliyor.
        assert response.status_code == 200


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
