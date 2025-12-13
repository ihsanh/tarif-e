"""
Token Generator
Şifre sıfırlama için güvenli token üretimi
"""
import secrets
import string
from itsdangerous import URLSafeTimedSerializer
from app.config import settings


def generate_reset_token(length: int = 32) -> str:
    """
    Güvenli rastgele token üret

    Args:
        length: Token uzunluğu (default 32)

    Returns:
        Hex string token
    """
    return secrets.token_urlsafe(length)


def generate_simple_token(length: int = 6) -> str:
    """
    Basit sayısal token üret (6 haneli kod gibi)

    Args:
        length: Token uzunluğu (default 6)

    Returns:
        Numeric string token
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


class TokenSerializer:
    """
    Timed token serializer
    Email verification, password reset için
    """

    def __init__(self, secret_key: str = None, salt: str = "password-reset"):
        self.secret_key = secret_key or settings.SECRET_KEY
        self.salt = salt
        self.serializer = URLSafeTimedSerializer(self.secret_key)

    def generate_token(self, data: dict) -> str:
        """
        Data'yı token'a çevir

        Args:
            data: Token'a eklenecek data (user_id, email vb.)

        Returns:
            Signed token string
        """
        return self.serializer.dumps(data, salt=self.salt)

    def verify_token(self, token: str, max_age: int = 3600) -> dict:
        """
        Token'ı doğrula ve data'yı çıkar

        Args:
            token: Doğrulanacak token
            max_age: Maksimum geçerlilik süresi (saniye)

        Returns:
            Token'dan çıkarılan data veya None
        """
        try:
            data = self.serializer.loads(
                token,
                salt=self.salt,
                max_age=max_age
            )
            return data
        except Exception as e:
            return None


# Global instance
reset_token_serializer = TokenSerializer(salt="password-reset")