"""
Health Check Routes
"""
from fastapi import APIRouter
from app.config import settings
from app.services.ai_service import ai_service

router = APIRouter(tags=["Health"])


@router.get("/api/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "ai_enabled": ai_service.enabled,
        "ai_mode": settings.AI_MODE
    }
