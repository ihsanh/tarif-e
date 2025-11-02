"""
Uygulama yapılandırma ayarları
"""
from pydantic_settings import BaseSettings
from typing import Optional


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
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = None
    
    # AI Settings
    AI_MODE: str = "auto"  # auto, manual, hybrid, off
    MAX_FREE_AI_REQUESTS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
