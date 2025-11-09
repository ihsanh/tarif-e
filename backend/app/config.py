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
    DATABASE_URL: str = "sqlite:///./data/tarif_e.db"
    
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

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
