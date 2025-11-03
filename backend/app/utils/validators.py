"""
Validasyon Fonksiyonları
"""
import re


def validate_email(email: str) -> bool:
    """Email formatını kontrol et"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    Şifre güvenliğini kontrol et
    
    Returns:
        (bool, str): (Geçerli mi, Hata mesajı)
    """
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalı"
    
    if not re.search(r'[A-Z]', password):
        return False, "Şifre en az bir büyük harf içermeli"
    
    if not re.search(r'[a-z]', password):
        return False, "Şifre en az bir küçük harf içermeli"
    
    if not re.search(r'[0-9]', password):
        return False, "Şifre en az bir rakam içermeli"
    
    return True, ""


def validate_miktar(miktar: float) -> bool:
    """Malzeme miktarını kontrol et"""
    return miktar > 0
