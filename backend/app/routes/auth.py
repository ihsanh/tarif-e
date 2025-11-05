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
            data={"sub": new_user.id, "username": new_user.username},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(new_user)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Kullanıcı oluşturulurken hata: {e}")
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
        data={"sub": user.id, "username": user.username},
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
    logger.info(f"Profil isteği: {current_user.username}")
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Kullanıcı çıkışı (frontend'de token silinecek)"""
    logger.info(f"Çıkış: {current_user.username}")
    return {
        "success": True,
        "message": "Başarıyla çıkış yapıldı"
    }
