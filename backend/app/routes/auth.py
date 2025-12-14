"""
Authentication Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.database import get_db
from app.models import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.schemas.auth import (
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse
)
from app.utils.token_generator import generate_reset_token
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı"""
    logger.info(f"Kayıt isteği: {user_data.username} ({user_data.email})")

    # Email kontrolü
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"Email zaten kayıtlı: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı"
        )

    # Username kontrolü
    existing_username = db.query(User).filter(User.username == user_data.username.lower()).first()
    if existing_username:
        logger.warning(f"Username zaten kayıtlı: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten alınmış"
        )

    # Yeni kullanıcı oluştur
    try:
        new_user = User(
            email=user_data.email,
            username=user_data.username.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"✅ Yeni kullanıcı oluşturuldu: {new_user.username} (ID: {new_user.id})")

        # Token oluştur
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(new_user.id), "username": new_user.username},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(new_user)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] User creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı oluşturulurken bir hata oluştu"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Kullanıcı girişi"""
    logger.info(f"Giriş isteği: {form_data.username}")

    # Kullanıcıyı bul (username veya email ile)
    user = db.query(User).filter(
        (User.username == form_data.username.lower()) | (User.email == form_data.username)
    ).first()

    if not user:
        logger.warning(f"Kullanıcı bulunamadı: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Şifre kontrolü
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Hatalı şifre denemesi: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Aktif kullanıcı kontrolü
    if not user.is_active:
        logger.warning(f"Pasif kullanıcı giriş denemesi: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız aktif değil"
        )

    # Token oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    logger.info(f"✅ Başarılı giriş: {user.username} (ID: {user.id})")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Mevcut kullanıcı bilgilerini getir"""
    logger.info(f"Profil isteği: {current_user.id}")
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Kullanıcı çıkışı (frontend'de token silinecek)"""
    logger.info(f"Çıkış: {current_user.id}")
    return {
        "success": True,
        "message": "Başarıyla çıkış yapıldı"
    }

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
        request: PasswordResetRequest,
        db: Session = Depends(get_db)
):
    """
    Şifre sıfırlama talebi

    - Email'e sıfırlama linki gönderir
    - Güvenlik için her zaman başarılı döner (email bilgisi sızdırmamak için)
    """
    try:
        # Kullanıcıyı bul
        user = db.query(User).filter(User.email == request.email).first()

        if user:
            # Reset token üret
            reset_token = generate_reset_token()

            # Token'ı veritabanına kaydet (30 dakika geçerli)
            user.set_reset_token(reset_token, expires_minutes=30)
            db.commit()

            # Reset linki oluştur
            # Production'da: https://tarif-e.com/reset-password?token=...
            # Development'ta: http://localhost:8000/reset-password?token=...
            reset_link = f"http://localhost:8000/login.html?token={reset_token}"

            # [DEV] Print reset link for development
            print("\n" + "=" * 60)
            print(f"[RESET LINK] {reset_link}")
            print("=" * 60 + "\n")

            # Email gönder
            await email_service.send_reset_email(
                to_email=user.email,
                reset_link=reset_link,
                username=user.username
            )

            logger.info(f"[INFO] Password reset requested for: {user.email}")
        else:
            # Güvenlik: Email bulunamadı bile bilgisini verme
            logger.warning(f"[WARN] Password reset requested for non-existent email: {request.email}")

        # Her zaman başarılı döner (email enumeration önleme)
        return PasswordResetResponse(
            success=True,
            message="Eğer bu email kayıtlıysa, şifre sıfırlama linki gönderildi."
        )

    except Exception as e:
        logger.error(f"[ERROR] Forgot password error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Şifre sıfırlama işlemi sırasında hata oluştu"
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
        request: PasswordResetConfirm,
        db: Session = Depends(get_db)
):
    """
    Şifre sıfırlama onayı

    - Token ile yeni şifreyi ayarlar
    """
    try:
        # Token ile kullanıcıyı bul
        user = db.query(User).filter(User.reset_token == request.token).first()

        if not user:
            raise HTTPException(
                status_code=400,
                detail="Geçersiz veya süresi dolmuş token"
            )

        # Token geçerliliğini kontrol et
        if not user.is_reset_token_valid(request.token):
            raise HTTPException(
                status_code=400,
                detail="Token süresi dolmuş. Lütfen yeni bir şifre sıfırlama talebi oluşturun."
            )

        # Yeni şifreyi hashle ve kaydet
        user.hashed_password = get_password_hash(request.new_password)

        # Token'ı temizle
        user.clear_reset_token()

        db.commit()

        logger.info(f"✅ Password reset successful for: {user.email}")

        return PasswordResetResponse(
            success=True,
            message="Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Reset password error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Şifre güncelleme sırasında hata oluştu"
        )


@router.get("/verify-reset-token/{token}")
async def verify_reset_token(
        token: str,
        db: Session = Depends(get_db)
):
    """
    Reset token'ın geçerliliğini kontrol et

    Frontend bu endpoint'i kullanarak token'ın geçerli olup olmadığını öğrenebilir
    """
    user = db.query(User).filter(User.reset_token == token).first()

    if not user or not user.is_reset_token_valid(token):
        return {
            "valid": False,
            "message": "Token geçersiz veya süresi dolmuş"
        }

    return {
        "valid": True,
        "message": "Token geçerli",
        "email": user.email  # Email'i göster (doğrulama için)
    }