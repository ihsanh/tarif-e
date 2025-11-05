"""
Tarif-e FastAPI Ana Uygulama - Güncellenmiş Versiyon
"""
import sys
from pathlib import Path
import logging

# Backend klasörünü Python path'ine ekle
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from app.config import settings
from app.database import engine
from app.models import Base
from app.routes import (
    health_router,
    malzeme_router,
    tarif_router,
    alisveris_router,
    auth_router
)
from app.logger_config import configure_logging

# Loglamayı başlat
configure_logging()

# Logger kurulumu
logger = logging.getLogger(__name__) # Uvicorn'un ana logger'ını kullanmak yaygın bir pratik

# Veritabanını başlat
# Not: init_db fonksiyonu init_db.py veya database.py içinde çağrılmalıdır.
# Burada Base.metadata.create_all(bind=engine) çağrısı doğru yerdir.
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Akıllı Mutfak Asistanı - Malzemeden Tarife, Tariften Alışverişe",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# Routes
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(malzeme_router)
app.include_router(tarif_router)
app.include_router(alisveris_router)


@app.get("/")
async def ana_sayfa():
    """Ana sayfa"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Tarif-e API",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/ayarlar")
async def ayarlar_getir():
    """Kullanıcı ayarlarını getir"""
    return {
        "ai_mode": settings.AI_MODE,
        "ai_quota": settings.MAX_FREE_AI_REQUESTS,
        "data_sharing": True
    }


@app.on_event("startup")
async def startup_event():
    """Uygulama başlarken"""
    logger.info("=" * 50)
    logger.info(f"🍳 {settings.APP_NAME} başlatılıyor...")
    logger.info(f"📊 Debug modu: {settings.DEBUG}")
    logger.info(f"🤖 AI aktif: {settings.AI_MODE != 'off'}")
    logger.info(f"⚙️  AI modu: {settings.AI_MODE}")
    # HOST ve PORT bilgileri uvicorn tarafından zaten loglanacağı için bu bilgiyi DEBUG seviyesine düşürebiliriz
    logger.debug(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📚 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 50)


if __name__ == "__main__":
    import uvicorn
    # uvicorn.run zaten loglama yaptığı için burada sadece çalıştırma kodunu bıraktık.
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )