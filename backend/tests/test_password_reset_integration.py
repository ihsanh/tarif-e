"""
Integration Tests - Password Reset API Endpoints
Test complete password reset flow end-to-end
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.database import Base, engine, get_db
from app.models.user import User
from app.utils.auth import get_password_hash


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def test_user(client):
    """Test kullanıcısı oluştur"""
    # Kayıt endpoint'i kullan
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "oldpass123",
        "full_name": "Test User"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200 or response.status_code == 201
    
    return user_data


class TestForgotPasswordEndpoint:
    """Forgot password endpoint testleri"""
    
    def test_forgot_password_success(self, client, test_user):
        """Kayıtlı email ile forgot password başarılı"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": test_user["email"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "email" in data["message"].lower() or "gönderildi" in data["message"].lower()
    
    def test_forgot_password_non_existent_email(self, client):
        """Olmayan email ile forgot password (güvenlik testi)"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        
        # Güvenlik: Aynı mesajı dönmeli (email enumeration önleme)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_forgot_password_invalid_email_format(self, client):
        """Geçersiz email formatı"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "invalid-email"}
        )
        
        # Pydantic validation error
        assert response.status_code == 422
    
    def test_forgot_password_creates_token(self, client, test_user):
        """Token database'e kaydediliyor mu?"""
        from app.database import SessionLocal
        
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": test_user["email"]}
        )
        
        assert response.status_code == 200
        
        # Database'den kullanıcıyı kontrol et
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        
        assert user is not None
        assert user.reset_token is not None
        assert user.reset_token_expires is not None
        
        # Token süresi kontrolü (yaklaşık 30 dakika)
        expected_time = datetime.utcnow() + timedelta(minutes=30)
        time_diff = abs((user.reset_token_expires - expected_time).total_seconds())
        assert time_diff < 60  # 1 dakika tolerans
        
        db.close()


class TestVerifyResetTokenEndpoint:
    """Verify reset token endpoint testleri"""
    
    def test_verify_valid_token(self, client, test_user):
        """Geçerli token doğrulanıyor mu?"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        
        # Token oluştur
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        # Token doğrula
        response = client.get(f"/api/auth/verify-reset-token/{token}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is True
        assert data["email"] == test_user["email"]
    
    def test_verify_invalid_token(self, client):
        """Geçersiz token reddediliyor mu?"""
        response = client.get("/api/auth/verify-reset-token/invalid-token-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
    
    def test_verify_expired_token(self, client, test_user):
        """Süresi dolmuş token reddediliyor mu?"""
        from app.database import SessionLocal
        
        # Süresi dolmuş token oluştur
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        
        token = "expired-token"
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
        db.close()
        
        # Token doğrula
        response = client.get(f"/api/auth/verify-reset-token/{token}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False


class TestResetPasswordEndpoint:
    """Reset password endpoint testleri"""
    
    def test_reset_password_success(self, client, test_user):
        """Başarılı şifre sıfırlama"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        
        # Token oluştur
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        # Şifre sıfırla
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "güncellendi" in data["message"].lower() or "updated" in data["message"].lower()
    
    def test_reset_password_invalid_token(self, client):
        """Geçersiz token ile şifre sıfırlama"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "newpass123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "geçersiz" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    def test_reset_password_expired_token(self, client, test_user):
        """Süresi dolmuş token ile şifre sıfırlama"""
        from app.database import SessionLocal
        
        # Süresi dolmuş token
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        
        token = "expired-token"
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        db.close()
        
        # Şifre sıfırla
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpass123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "dolmuş" in data["detail"].lower() or "expired" in data["detail"].lower()
    
    def test_reset_password_short_password(self, client, test_user):
        """Kısa şifre validasyonu"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "abc"  # 3 karakter
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_reset_password_no_letter(self, client, test_user):
        """Harf içermeyen şifre validasyonu"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "123456"  # Sadece rakam
            }
        )
        
        assert response.status_code == 422
    
    def test_reset_password_no_digit(self, client, test_user):
        """Rakam içermeyen şifre validasyonu"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "abcdef"  # Sadece harf
            }
        )
        
        assert response.status_code == 422
    
    def test_reset_password_token_cleared_after_use(self, client, test_user):
        """Token kullanıldıktan sonra temizleniyor mu?"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        # İlk kullanım - başarılı
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpass123"
            }
        )
        assert response.status_code == 200
        
        # Token temizlendi mi kontrol et
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        assert user.reset_token is None
        assert user.reset_token_expires is None
        db.close()
    
    def test_reset_password_updates_database(self, client, test_user):
        """Şifre database'de güncelleniyor mu?"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        from app.utils.auth import verify_password
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        old_hashed_password = user.hashed_password
        
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        # Şifre sıfırla
        new_password = "brandnewpass123"
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": new_password
            }
        )
        assert response.status_code == 200
        
        # Database'de şifre güncellenmiş mi?
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        
        assert user.hashed_password != old_hashed_password
        assert verify_password(new_password, user.hashed_password)
        
        db.close()


class TestPasswordResetFlow:
    """End-to-end password reset flow"""
    
    def test_complete_password_reset_flow(self, client):
        """Tam şifre sıfırlama akışı"""
        # 1. Kullanıcı kayıt
        user_data = {
            "email": "flowtest@example.com",
            "username": "flowtest",
            "password": "oldpass123"
        }
        
        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code in [200, 201]
        
        # 2. Forgot password
        forgot_response = client.post(
            "/api/auth/forgot-password",
            json={"email": user_data["email"]}
        )
        assert forgot_response.status_code == 200
        
        # 3. Database'den token al
        from app.database import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter(User.email == user_data["email"]).first()
        token = user.reset_token
        assert token is not None
        db.close()
        
        # 4. Token doğrula
        verify_response = client.get(f"/api/auth/verify-reset-token/{token}")
        assert verify_response.status_code == 200
        assert verify_response.json()["valid"] is True
        
        # 5. Yeni şifre ayarla
        reset_response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpass123"
            }
        )
        assert reset_response.status_code == 200
        
        # 6. Eski şifre ile giriş denemesi - başarısız olmalı
        from fastapi import Form
        old_login = client.post(
            "/api/auth/login",
            data={"username": user_data["email"], "password": "oldpass123"}
        )
        assert old_login.status_code == 401 or old_login.status_code == 400
        
        # 7. Yeni şifre ile giriş - başarılı olmalı
        new_login = client.post(
            "/api/auth/login",
            data={"username": user_data["email"], "password": "newpass123"}
        )
        assert new_login.status_code == 200
        assert "access_token" in new_login.json()
    
    def test_token_single_use(self, client, test_user):
        """Token tek kullanımlık mı?"""
        from app.database import SessionLocal
        from app.utils.token_generator import generate_reset_token
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_user["email"]).first()
        token = generate_reset_token()
        user.set_reset_token(token, expires_minutes=30)
        db.commit()
        db.close()
        
        # İlk kullanım - başarılı
        response1 = client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": "newpass123"}
        )
        assert response1.status_code == 200
        
        # İkinci kullanım - başarısız olmalı
        response2 = client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": "anotherpass123"}
        )
        assert response2.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
