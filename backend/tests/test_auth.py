"""
Authentication Tests - Login, Register, Token testleri
Düzeltilmiş: conftest.py kullanır
"""
import pytest

# ❌ BUNLARI KALDIR - conftest.py halledecek
# from fastapi.testclient import TestClient
# from app.main import app
# from app.database import Base, engine
# client = TestClient(app)


class TestRegister:
    """Kullanıcı kayıt testleri"""

    def test_register_basarili(self, client):
        """Başarılı kayıt"""
        data = {
            "email": "test_register@example.com",
            "username": "test_register_user",
            "password": "test123",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=data)

        assert response.status_code == 201
        result = response.json()
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["user"]["username"] == "test_register_user"
        assert result["user"]["email"] == "test_register@example.com"

    def test_register_duplicate_email(self, client):
        """Aynı email ile ikinci kayıt - hata vermeli"""
        data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "test123"
        }
        # İlk kayıt
        client.post("/api/auth/register", json=data)

        # İkinci kayıt - farklı username ama aynı email
        data2 = {
            "email": "duplicate@example.com",  # Aynı email
            "username": "user2",
            "password": "test123"
        }
        response = client.post("/api/auth/register", json=data2)

        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client):
        """Aynı username ile ikinci kayıt - hata vermeli"""
        data = {
            "email": "user1@example.com",
            "username": "duplicate_user",
            "password": "test123"
        }
        # İlk kayıt
        client.post("/api/auth/register", json=data)

        # İkinci kayıt - farklı email ama aynı username
        data2 = {
            "email": "user2@example.com",
            "username": "duplicate_user",  # Aynı username
            "password": "test123"
        }
        response = client.post("/api/auth/register", json=data2)

        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Geçersiz email formatı"""
        data = {
            "email": "invalid-email",  # @ yok
            "username": "testuser",
            "password": "test123"
        }
        response = client.post("/api/auth/register", json=data)

        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client):
        """Kısa şifre - min 6 karakter"""
        data = {
            "email": "short@example.com",
            "username": "shortpass",
            "password": "123"  # 3 karakter
        }
        response = client.post("/api/auth/register", json=data)

        assert response.status_code == 422  # Validation error


class TestLogin:
    """Login testleri"""

    def test_login_basarili_email(self, client):
        """Email ile başarılı login"""
        # Önce kayıt ol
        register_data = {
            "email": "login_email@example.com",
            "username": "login_email_user",
            "password": "test123"
        }
        client.post("/api/auth/register", json=register_data)

        # Login yap - EMAIL ile
        login_data = {
            "username": "login_email@example.com",  # Email kullanılabilir
            "password": "test123"
        }
        response = client.post("/api/auth/login", data=login_data)  # data= not json=

        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert result["user"]["email"] == "login_email@example.com"

    def test_login_basarili_username(self, client):
        """Username ile başarılı login"""
        # Önce kayıt ol
        register_data = {
            "email": "login_username@example.com",
            "username": "login_username_user",
            "password": "test123"
        }
        client.post("/api/auth/register", json=register_data)

        # Login yap - USERNAME ile
        login_data = {
            "username": "login_username_user",
            "password": "test123"
        }
        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert result["user"]["username"] == "login_username_user"

    def test_login_yanlis_sifre(self, client):
        """Yanlış şifre ile login"""
        # Önce kayıt ol
        register_data = {
            "email": "wrong_pass@example.com",
            "username": "wrong_pass_user",
            "password": "test123"
        }
        client.post("/api/auth/register", json=register_data)

        # Yanlış şifre ile login
        login_data = {
            "username": "wrong_pass_user",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == 401
        assert "şifre" in response.json()["detail"].lower()

    def test_login_olmayan_kullanici(self, client):
        """Olmayan kullanıcı ile login"""
        login_data = {
            "username": "nonexistent_user_12345",
            "password": "test123"
        }
        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == 401
        assert "kullanıcı" in response.json()["detail"].lower()


class TestTokenValidation:
    """Token doğrulama testleri"""

    def test_gecerli_token_ile_api_erisim(self, client):
        """Geçerli token ile API erişimi"""
        # Kayıt ol ve token al
        register_data = {
            "email": "token_test@example.com",
            "username": "token_test_user",
            "password": "test123"
        }
        register_response = client.post("/api/auth/register", json=register_data)
        token = register_response.json()["access_token"]

        # Token ile malzeme listesine eriş
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/malzeme/liste", headers=headers)

        assert response.status_code == 200

    def test_gecersiz_token_ile_api_erisim(self, client):
        """Geçersiz token ile API erişimi - 401 dönmeli"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/malzeme/liste", headers=headers)

        assert response.status_code == 401

    def test_token_olmadan_api_erisim(self, client):
        """Token olmadan API erişimi - 401 dönmeli"""
        response = client.get("/api/malzeme/liste")

        assert response.status_code == 401


class TestUserProfile:
    """Kullanıcı profil testleri"""

    def test_me_endpoint(self, client):
        """Mevcut kullanıcı bilgisi"""
        # Kayıt ol
        register_data = {
            "email": "profile@example.com",
            "username": "profile_user",
            "password": "test123",
            "full_name": "Profile Test User"
        }
        register_response = client.post("/api/auth/register", json=register_data)
        token = register_response.json()["access_token"]

        # Profil bilgisi al
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        user = response.json()
        assert user["username"] == "profile_user"
        assert user["email"] == "profile@example.com"
        assert user["full_name"] == "Profile Test User"

    def test_me_endpoint_without_token(self, client):
        """Token olmadan profil bilgisi - 401"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401


class TestLogout:
    """Logout testleri"""

    def test_logout_basarili(self, client):
        """Başarılı logout"""
        # Kayıt ol
        register_data = {
            "email": "logout@example.com",
            "username": "logout_user",
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
