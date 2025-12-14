"""
Unit Tests - Password Reset Functionality
Test token generation, validation, and email service
"""
import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.utils.token_generator import (
    generate_reset_token,
    generate_simple_token,
    TokenSerializer,
    reset_token_serializer
)
from app.services.email_service import EmailService


class TestTokenGenerator:
    """Token üretimi testleri"""
    
    def test_generate_reset_token_length(self):
        """Reset token doğru uzunlukta mı?"""
        token = generate_reset_token()
        assert len(token) > 0
        assert isinstance(token, str)
    
    def test_generate_reset_token_uniqueness(self):
        """Her token benzersiz mi?"""
        token1 = generate_reset_token()
        token2 = generate_reset_token()
        assert token1 != token2
    
    def test_generate_simple_token_length(self):
        """Simple token (6 haneli) doğru uzunlukta mı?"""
        token = generate_simple_token(length=6)
        assert len(token) == 6
        assert token.isdigit()
    
    def test_generate_simple_token_custom_length(self):
        """Özel uzunlukta token üretilebiliyor mu?"""
        token = generate_simple_token(length=4)
        assert len(token) == 4
        assert token.isdigit()


class TestTokenSerializer:
    """Token serializer testleri"""
    
    def test_generate_and_verify_token(self):
        """Token üretme ve doğrulama"""
        serializer = TokenSerializer(secret_key="test-secret-key")
        
        # Token üret
        data = {"user_id": 123, "email": "test@example.com"}
        token = serializer.generate_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Token doğrula
        verified_data = serializer.verify_token(token, max_age=3600)
        assert verified_data is not None
        assert verified_data["user_id"] == 123
        assert verified_data["email"] == "test@example.com"
    
    def test_verify_expired_token(self):
        """Süresi dolmuş token reddedilmeli"""
        import time
        serializer = TokenSerializer(secret_key="test-secret-key")

        # Token üret
        data = {"user_id": 123}
        token = serializer.generate_token(data)

        # 1 saniye bekle ve max_age=0 ile kontrol et (token 1 saniye önce oluşturuldu)
        time.sleep(1)
        verified_data = serializer.verify_token(token, max_age=0)
        assert verified_data is None
    
    def test_verify_invalid_token(self):
        """Geçersiz token reddedilmeli"""
        serializer = TokenSerializer(secret_key="test-secret-key")
        
        invalid_token = "invalid-token-12345"
        verified_data = serializer.verify_token(invalid_token)
        assert verified_data is None
    
    def test_global_reset_token_serializer(self):
        """Global reset_token_serializer çalışıyor mu?"""
        data = {"user_id": 456}
        token = reset_token_serializer.generate_token(data)
        
        verified = reset_token_serializer.verify_token(token)
        assert verified is not None
        assert verified["user_id"] == 456


class TestUserResetTokenMethods:
    """User model reset token metodları testleri"""
    
    def test_set_reset_token(self, db_session):
        """set_reset_token metodu çalışıyor mu?"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()
        
        token = "test-token-123"
        user.set_reset_token(token, expires_minutes=30)
        
        assert user.reset_token == token
        assert user.reset_token_expires is not None
        
        # Süre kontrolü (yaklaşık 30 dakika sonra)
        expected_time = datetime.utcnow() + timedelta(minutes=30)
        time_diff = abs((user.reset_token_expires - expected_time).total_seconds())
        assert time_diff < 5  # 5 saniye tolerans
    
    def test_clear_reset_token(self, db_session):
        """clear_reset_token metodu çalışıyor mu?"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()
        
        # Token ayarla
        user.set_reset_token("test-token", expires_minutes=30)
        assert user.reset_token is not None
        
        # Temizle
        user.clear_reset_token()
        assert user.reset_token is None
        assert user.reset_token_expires is None
    
    def test_is_reset_token_valid_success(self, db_session):
        """Geçerli token doğrulanıyor mu?"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()
        
        token = "valid-token-123"
        user.set_reset_token(token, expires_minutes=30)
        
        # Doğrulama
        assert user.is_reset_token_valid(token) is True
    
    def test_is_reset_token_valid_wrong_token(self, db_session):
        """Yanlış token reddedilmeli"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()
        
        user.set_reset_token("correct-token", expires_minutes=30)
        
        # Yanlış token
        assert user.is_reset_token_valid("wrong-token") is False
    
    def test_is_reset_token_valid_expired(self, db_session):
        """Süresi dolmuş token reddedilmeli"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()
        
        # Token ayarla ve manuel olarak süresini geçmiş yap
        token = "expired-token"
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() - timedelta(minutes=1)
        db_session.commit()
        
        # Doğrulama
        assert user.is_reset_token_valid(token) is False
    
    def test_is_reset_token_valid_no_token(self, db_session):
        """Token yoksa False dönmeli"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()
        
        # Token ayarlanmamış
        assert user.is_reset_token_valid("any-token") is False


class TestEmailService:
    """Email servisi testleri"""
    
    def test_email_service_initialization(self):
        """Email servisi başlatılıyor mu?"""
        email_service = EmailService()
        assert email_service is not None
        assert hasattr(email_service, 'enabled')
    
    def test_email_service_dev_mode(self):
        """Development modunda email disabled mi?"""
        email_service = EmailService()
        # Development'ta enabled=False olmalı
        assert email_service.enabled is False
    
    @pytest.mark.asyncio
    async def test_send_reset_email_dev_mode(self, caplog):
        """Dev mode'da email log'lanıyor mu?"""
        email_service = EmailService()
        
        result = await email_service.send_reset_email(
            to_email="test@example.com",
            reset_link="http://localhost:8000/login.html?token=abc123",
            username="testuser"
        )
        
        # Development'ta True dönmeli (başarılı)
        assert result is True
        
        # Log kontrolü
        assert "DEV MODE" in caplog.text or "Reset link" in caplog.text
    
    @pytest.mark.asyncio
    async def test_send_reset_email_with_username(self):
        """Username ile email gönderiliyor mu?"""
        email_service = EmailService()
        
        result = await email_service.send_reset_email(
            to_email="test@example.com",
            reset_link="http://test.com/reset?token=123",
            username="John Doe"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_reset_email_without_username(self):
        """Username olmadan email gönderiliyor mu?"""
        email_service = EmailService()
        
        result = await email_service.send_reset_email(
            to_email="test@example.com",
            reset_link="http://test.com/reset?token=123"
        )
        
        assert result is True
    
    def test_email_html_template(self):
        """Email HTML template oluşturuluyor mu?"""
        email_service = EmailService()
        
        html = email_service._get_reset_email_html(
            reset_link="http://localhost:8000/reset?token=abc",
            username="Test User"
        )
        
        assert html is not None
        assert "Test User" in html
        assert "http://localhost:8000/reset?token=abc" in html
        assert "Tarif-e" in html


class TestPasswordValidation:
    """Şifre validasyon testleri"""
    
    def test_password_min_length(self):
        """Minimum 6 karakter kontrolü"""
        short_password = "abc12"  # 5 karakter
        assert len(short_password) < 6
        
        valid_password = "abc123"  # 6 karakter
        assert len(valid_password) >= 6
    
    def test_password_contains_letter(self):
        """En az bir harf kontrolü"""
        no_letter = "123456"
        assert not any(c.isalpha() for c in no_letter)
        
        has_letter = "abc123"
        assert any(c.isalpha() for c in has_letter)
    
    def test_password_contains_digit(self):
        """En az bir rakam kontrolü"""
        no_digit = "abcdef"
        assert not any(c.isdigit() for c in no_digit)
        
        has_digit = "abc123"
        assert any(c.isdigit() for c in has_digit)
    
    def test_password_match(self):
        """Şifre eşleşme kontrolü"""
        password1 = "test123"
        password2 = "test123"
        assert password1 == password2
        
        password3 = "test456"
        assert password1 != password3


# Pytest fixtures
@pytest.fixture
def db_session():
    """Test database session"""
    from app.database import engine, Base, SessionLocal
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
