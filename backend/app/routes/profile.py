"""
Kullanıcı Profil ve Ayarlar Routes
backend/app/routes/profile.py
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.models.user_profile import UserProfile
from app.utils.auth import get_current_user, get_password_hash, verify_password
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import logging
import shutil
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["Profil"])


# ============================================
# SCHEMAS
# ============================================

class PasswordChange(BaseModel):
    """Şifre değişikliği şeması"""
    current_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    """Profil güncelleme şeması"""
    bio: Optional[str] = None
    dietary_preferences: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    dislikes: Optional[List[str]] = None
    theme: Optional[str] = None
    language: Optional[str] = None


class UserUpdate(BaseModel):
    """Kullanıcı bilgileri güncelleme"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


# ============================================
# ENDPOINTS
# ============================================

@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının profil bilgilerini getir"""
    
    # Profil yoksa oluştur
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            dietary_preferences=[],
            allergies=[],
            dislikes=[],
            theme="light",
            language="tr"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        },
        "profile": {
            "bio": profile.bio,
            "profile_photo_url": profile.profile_photo_url,
            "dietary_preferences": profile.dietary_preferences or [],
            "allergies": profile.allergies or [],
            "dislikes": profile.dislikes or [],
            "theme": profile.theme,
            "language": profile.language
        }
    }


@router.put("/update")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Profil ayarlarını güncelle"""
    
    # Profil yoksa oluştur
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Güncellemeleri uygula
    if profile_data.bio is not None:
        profile.bio = profile_data.bio
    
    if profile_data.dietary_preferences is not None:
        profile.dietary_preferences = profile_data.dietary_preferences
    
    if profile_data.allergies is not None:
        profile.allergies = profile_data.allergies
    
    if profile_data.dislikes is not None:
        profile.dislikes = profile_data.dislikes
    
    if profile_data.theme is not None:
        if profile_data.theme not in ["light", "dark", "auto"]:
            raise HTTPException(status_code=400, detail="Geçersiz tema")
        profile.theme = profile_data.theme
    
    if profile_data.language is not None:
        profile.language = profile_data.language
    
    db.commit()
    db.refresh(profile)
    
    logger.info(f"Kullanıcı {current_user.id} profil ayarlarını güncelledi")
    
    return {
        "success": True,
        "message": "Profil başarıyla güncellendi",
        "profile": {
            "bio": profile.bio,
            "dietary_preferences": profile.dietary_preferences,
            "allergies": profile.allergies,
            "dislikes": profile.dislikes,
            "theme": profile.theme,
            "language": profile.language
        }
    }


@router.put("/user-info")
async def update_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcı temel bilgilerini güncelle"""
    
    # Email değişikliği kontrolü
    if user_data.email and user_data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Bu email adresi zaten kullanılıyor")
        current_user.email = user_data.email
    
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    
    db.commit()
    
    logger.info(f"Kullanıcı {current_user.id} temel bilgilerini güncelledi")
    
    return {
        "success": True,
        "message": "Bilgiler başarıyla güncellendi",
        "user": {
            "email": current_user.email,
            "full_name": current_user.full_name
        }
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Şifre değiştir"""
    
    # Mevcut şifreyi doğrula
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre yanlış")
    
    # Yeni şifre kontrolü
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")
    
    if password_data.new_password == password_data.current_password:
        raise HTTPException(status_code=400, detail="Yeni şifre eskisiyle aynı olamaz")
    
    # Şifreyi güncelle
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(f"Kullanıcı {current_user.id} şifresini değiştirdi")
    
    return {
        "success": True,
        "message": "Şifre başarıyla değiştirildi"
    }


@router.post("/upload-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Profil fotoğrafı yükle"""
    
    # Dosya tipi kontrolü
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Sadece JPEG, PNG ve WebP formatları destekleniyor"
        )
    
    # Dosya boyutu kontrolü (5MB)
    file.file.seek(0, 2)  # Dosya sonuna git
    file_size = file.file.tell()  # Boyutu al
    file.file.seek(0)  # Başa dön
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="Dosya boyutu 5MB'dan küçük olmalı")
    
    # Dosya adı oluştur
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"profile_{current_user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    
    # Klasör oluştur
    upload_dir = Path("static/profile_photos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Dosyayı kaydet
    file_path = upload_dir / unique_filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # URL oluştur
    photo_url = f"/static/profile_photos/{unique_filename}"
    
    # Profil güncelle
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Eski fotoğrafı sil (varsa)
    if profile.profile_photo_url:
        old_path = Path("." + profile.profile_photo_url)
        if old_path.exists():
            old_path.unlink()
    
    profile.profile_photo_url = photo_url
    db.commit()
    
    logger.info(f"Kullanıcı {current_user.id} profil fotoğrafını güncelledi")
    
    return {
        "success": True,
        "message": "Profil fotoğrafı başarıyla yüklendi",
        "photo_url": photo_url
    }


@router.delete("/delete-photo")
async def delete_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Profil fotoğrafını sil"""
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile or not profile.profile_photo_url:
        raise HTTPException(status_code=404, detail="Profil fotoğrafı bulunamadı")
    
    # Dosyayı sil
    file_path = Path("." + profile.profile_photo_url)
    if file_path.exists():
        file_path.unlink()
    
    profile.profile_photo_url = None
    db.commit()
    
    logger.info(f"Kullanıcı {current_user.id} profil fotoğrafını sildi")
    
    return {
        "success": True,
        "message": "Profil fotoğrafı silindi"
    }


@router.get("/dietary-options")
async def get_dietary_options():
    """Mevcut diyet seçeneklerini getir"""
    return {
        "success": True,
        "options": {
            "dietary_preferences": [
                {"value": "vegan", "label": "Vegan", "icon": "🌱"},
                {"value": "vegetarian", "label": "Vejetaryen", "icon": "🥗"},
                {"value": "pescatarian", "label": "Pesko-vejetaryen", "icon": "🐟"},
                {"value": "glutensiz", "label": "Glutensiz", "icon": "🌾"},
                {"value": "laktoz-intolerans", "label": "Laktozsuz", "icon": "🥛"},
                {"value": "keto", "label": "Ketojenik", "icon": "🥑"},
                {"value": "paleo", "label": "Paleo", "icon": "🍖"},
                {"value": "halal", "label": "Helal", "icon": "☪️"},
                {"value": "kosher", "label": "Koşer", "icon": "✡️"},
                {"value": "dusuk-karbonhidrat", "label": "Düşük Karbonhidrat", "icon": "🥦"}
            ],
            "common_allergies": [
                {"value": "fistik", "label": "Fıstık", "icon": "🥜"},
                {"value": "agac-fistiği", "label": "Ağaç Fıstığı", "icon": "🌰"},
                {"value": "sut", "label": "Süt Ürünleri", "icon": "🥛"},
                {"value": "yumurta", "label": "Yumurta", "icon": "🥚"},
                {"value": "soya", "label": "Soya", "icon": "🫘"},
                {"value": "bugday", "label": "Buğday", "icon": "🌾"},
                {"value": "balik", "label": "Balık", "icon": "🐟"},
                {"value": "kabuklu-deniz", "label": "Kabuklu Deniz Ürünleri", "icon": "🦐"},
                {"value": "susam", "label": "Susam", "icon": "🌰"},
                {"value": "hardal", "label": "Hardal", "icon": "🌭"}
            ],
            "themes": [
                {"value": "light", "label": "Açık Tema", "icon": "☀️"},
                {"value": "dark", "label": "Koyu Tema", "icon": "🌙"},
                {"value": "auto", "label": "Otomatik", "icon": "🔄"}
            ]
        }
    }
