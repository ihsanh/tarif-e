"""
Authentication Utilities
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

# Password hashing - bcrypt 4.0+ compatibility
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b"  # Force bcrypt 2b variant (compatible with bcrypt 4.0+)
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT settings
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 gün

# Logger nesnesi oluşturma
logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifreyi doğrula"""
    # Bcrypt max 72 byte kabul eder - byte seviyesinde kes
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Byte seviyesinde kes ve geri decode et
        password_bytes = password_bytes[:72]
        # Geçerli UTF-8 karakterine kadar geri git
        while password_bytes:
            try:
                plain_password = password_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                password_bytes = password_bytes[:-1]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Şifreyi hashle"""
    # Bcrypt max 72 byte kabul eder - byte seviyesinde kes
    password_bytes = password.encode('utf-8')
    logger.debug(f"[AUTH] Password length: {len(password_bytes)} bytes")

    if len(password_bytes) > 72:
        # Byte seviyesinde kes ve geri decode et
        password_bytes = password_bytes[:72]
        # Geçerli UTF-8 karakterine kadar geri git
        while password_bytes:
            try:
                password = password_bytes.decode('utf-8')
                logger.debug(f"[AUTH] Password truncated to: {len(password_bytes)} bytes")
                break
            except UnicodeDecodeError:
                password_bytes = password_bytes[:-1]

    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"[ERROR] Failed to hash password: {e}")
        # Son çare olarak: şifreyi byte limitine tam olarak kes
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT token oluştur"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"✅ Token decode edildi: {payload}" ) # DEBUG
        return payload
    except Exception as e:
        logger.error(f"❌ Token decode hatası: {e}" )
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Mevcut kullanıcıyı getir (token'dan)"""
    from app.models import User

    logger.info(f"🔑 Token alındı: {token[:20]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    logger.info(f"📦 Payload: {payload}")
    if payload is None:
        logger.info("❌ Payload None!")
        raise credentials_exception

    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı aktif değil"
        )

    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Aktif kullanıcıyı getir"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Kullanıcı aktif değil")
    return current_user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Mevcut kullanıcıyı getir (opsiyonel - login olmadan da çalışır)"""
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None