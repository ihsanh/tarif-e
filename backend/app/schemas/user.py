"""
User Schemas - Authentication
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """Kullanıcı kayıt isteği"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Username sadece harf, rakam ve alt çizgi içerebilir"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username sadece harf, rakam ve alt çizgi içerebilir')
        return v.lower()
    
    @validator('password')
    def password_strength(cls, v):
        """Şifre en az 6 karakter olmalı"""
        if len(v) < 6:
            raise ValueError('Şifre en az 6 karakter olmalı')
        return v


class UserLogin(BaseModel):
    """Kullanıcı giriş isteği"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Kullanıcı response"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Token içindeki data"""
    user_id: Optional[int] = None
    username: Optional[str] = None
