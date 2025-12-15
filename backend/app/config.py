"""
Uygulama yapılandırma ayarları
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # Uygulama
    APP_NAME: str = "Tarif-e"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/tarif_e2.db"
    DATABASE_URL_TEST: str = "sqlite:///./data/test_tarif_e.db"
    
    # Security
    SECRET_KEY: str = "qTuW8SYKzlZZRI_otbnrtf3MyUcfzebi35ZN-gTMFOw"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = None
    
    # AI Settings
    AI_MODE: str = "auto"  # auto, manual, hybrid, off
    MAX_FREE_AI_REQUESTS: int = 10
    LOG_LEVEL: str = "DEBUG"

    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-please")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 gün

    # Email settings (opsiyonel - production için)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@tarif-e.com"
    SMTP_FROM_NAME: str = "Tarif-e"

    # Frontend URL (reset link için)
    FRONTEND_URL: str = "http://localhost:8000"

    # Subscription settings
    STANDARD_DAILY_RECIPE_LIMIT: int = 3  # Standart paket günlük tarif limiti
    PRO_MONTHLY_PRICE: float = 99.90  # Pro paket aylık ücret (TL)
    PRO_YEARLY_PRICE: float = 999.90  # Pro paket yıllık ücret (TL)
    DEFAULT_SUBSCRIPTION_TIER: str = "standard"  # Yeni kullanıcılar için varsayılan paket

    # Ads settings
    ADS_ENABLED: bool = True  # Reklamları aktif et/kapat
    GOOGLE_ADSENSE_CLIENT_ID: Optional[str] = "ca-pub-5031698187492956"  # Google AdSense Publisher ID (ca-pub-XXXXXXXX)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
