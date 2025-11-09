"""
Tarif-e FastAPI Ana Uygulama
"""
import sys
from pathlib import Path

# Backend klasörünü Python path'ine ekle
BACKEND_DIR = Path(__file__).parent.parent.resolve()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

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
    auth_router  # YENİ
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

# Frontend path
frontend_path = BACKEND_DIR.parent / "frontend"

# API Routes (önce bunlar)
app.include_router(health_router)
app.include_router(auth_router)  # YENİ - Authentication
app.include_router(malzeme_router)
app.include_router(tarif_router)
app.include_router(alisveris_router)


# HTML Pages (API route'larından sonra)
@app.get("/login.html")
async def login_page():
    """Login sayfası"""
    login_path = frontend_path / "login.html"
    if login_path.exists():
        return FileResponse(login_path)
    return {"error": "Login sayfası bulunamadı", "path": str(login_path)}


@app.get("/token_test.html")
async def token_test_page():
    """Token test sayfası"""
    test_path = frontend_path / "token_test.html"
    if test_path.exists():
        return FileResponse(test_path)
    return {"error": "Token test sayfası bulunamadı", "path": str(test_path)}


@app.get("/index.html")
async def index_page():
    """Ana sayfa"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Ana sayfa bulunamadı"}


@app.get("/")
async def root():
    """Root - Ana sayfaya yönlendir"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Tarif-e API",
        "docs": "/docs",
        "health": "/api/health"
    }


# Static files (CSS, JS, images) - en sonda
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


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
    print(f"🔐 Login: http://{settings.HOST}:{settings.PORT}/login.html")
    print(f"🧪 Token Test: http://{settings.HOST}:{settings.PORT}/token_test.html")
    print(f"📁 Frontend: {frontend_path}")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
