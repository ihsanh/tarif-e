"""
Tarif-e FastAPI Ana Uygulama
"""
import sys
from pathlib import Path

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
    alisveris_router
)

# Veritabanını başlat
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
    print("=" * 50)
    print(f"🍳 {settings.APP_NAME} başlatılıyor...")
    print(f"📊 Debug modu: {settings.DEBUG}")
    print(f"🤖 AI aktif: {settings.AI_MODE != 'off'}")
    print(f"⚙️  AI modu: {settings.AI_MODE}")
    print(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )