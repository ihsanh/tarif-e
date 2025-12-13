from pydantic import BaseModel, EmailStr, validator
import re


class PasswordResetRequest(BaseModel):
    """Şifre sıfırlama talebi"""
    email: EmailStr

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Şifre sıfırlama onayı"""
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Şifre en az 6 karakter olmalı')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Şifre en az bir harf içermeli')
        if not re.search(r'\d', v):
            raise ValueError('Şifre en az bir rakam içermeli')
        return v

    class Config:
        schema_extra = {
            "example": {
                "token": "abc123...",
                "new_password": "yeniSifre123"
            }
        }


class PasswordResetResponse(BaseModel):
    """Şifre sıfırlama yanıtı"""
    success: bool
    message: str