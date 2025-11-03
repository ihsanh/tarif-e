"""
Health Check Routes - Güncellenmiş Versiyon
"""
from fastapi import APIRouter
from app.config import settings
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/api/health")
async def health_check():
    """Sağlık kontrolü"""
    # Health check'ler genellikle sık çalıştığı için sadece DEBUG seviyesinde loglanabilir.
    logger.debug(f"Sağlık kontrolü yapıldı. AI durumu: {ai_service.enabled}")

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "ai_enabled": ai_service.enabled,
        "ai_mode": settings.AI_MODE
    }