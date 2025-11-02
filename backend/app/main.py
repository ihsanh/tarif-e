"""
Tarif-e FastAPI Ana Uygulama
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
from pathlib import Path

from .config import settings
from .database import engine, Base, get_db, init_db
from .services.ai_service import ai_service

# Veritabanını başlat
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Akıllı Mutfak Asistanı - Malzemeden Tarife, Tariften Alışverişe",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme için, production'da değiştir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files ve uploads klasörü
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Frontend klasörünü mount et
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# Pydantic models (request/response)
from pydantic import BaseModel

class MalzemeEkle(BaseModel):
    name: str
    miktar: Optional[float] = 1.0
    birim: Optional[str] = "adet"

class TarifOner(BaseModel):
    malzemeler: List[str]
    sure: Optional[int] = None
    zorluk: Optional[str] = None
    kategori: Optional[str] = None


# Routes

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa():
    """Ana sayfa"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return """
    <html>
        <head><title>Tarif-e</title></head>
        <body>
            <h1>🍳 Tarif-e - Akıllı Mutfak Asistanı</h1>
            <p>API çalışıyor! Frontend dosyaları yükleniyor...</p>
            <p>API Dokümantasyonu: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "ai_enabled": ai_service.enabled,
        "ai_mode": settings.AI_MODE
    }


@app.post("/api/malzeme/tani")
async def malzeme_tani(file: UploadFile = File(...)):
    """
    Fotoğraftan malzeme tanıma
    
    - AI kullanarak fotoğraftaki malzemeleri tespit eder
    - Kullanıcı ayarlarına göre AI kullanımı kontrol edilir
    """
    if not ai_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. GEMINI_API_KEY ayarlanmalı."
        )
    
    try:
        # Dosyayı kaydet
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # AI ile malzemeleri tanı
        malzemeler = ai_service.malzeme_tani(str(file_path))
        
        # Dosyayı sil (opsiyonel - veya sakla)
        # file_path.unlink()
        
        return {
            "success": True,
            "malzemeler": malzemeler,
            "count": len(malzemeler)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/malzeme/ekle")
async def malzeme_ekle(malzeme: MalzemeEkle, db: Session = Depends(get_db)):
    """
    Manuel malzeme ekleme
    
    - Kullanıcı malzemeyi kendin yazar
    - AI kullanmadan direkt ekleme
    """
    # TODO: Veritabanına kaydet
    return {
        "success": True,
        "message": f"{malzeme.name} eklendi",
        "malzeme": malzeme.dict()
    }


@app.get("/api/malzeme/liste")
async def malzeme_liste(db: Session = Depends(get_db)):
    """
    Kullanıcının malzeme listesi
    
    - Şu an için basit mock data
    - TODO: Veritabanından çek
    """
    # Mock data
    return {
        "malzemeler": [
            {"name": "domates", "miktar": 5, "birim": "adet"},
            {"name": "biber", "miktar": 3, "birim": "adet"},
            {"name": "soğan", "miktar": 2, "birim": "adet"},
        ]
    }


@app.post("/api/tarif/oner")
async def tarif_oner(request: TarifOner):
    """
    Malzemelerden tarif öner
    
    - AI kullanarak tarif üretir
    - Kullanıcı tercihlerini dikkate alır
    """
    if not ai_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. Manuel tarif ekleyin."
        )
    
    try:
        preferences = {}
        if request.sure:
            preferences['sure'] = request.sure
        if request.zorluk:
            preferences['zorluk'] = request.zorluk
        if request.kategori:
            preferences['kategori'] = request.kategori
        
        tarif = ai_service.tarif_oner(request.malzemeler, preferences)
        
        return {
            "success": True,
            "tarif": tarif
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tarif/{tarif_id}")
async def tarif_detay(tarif_id: int, db: Session = Depends(get_db)):
    """
    Tarif detayı
    
    - TODO: Veritabanından tarif getir
    """
    # Mock data
    return {
        "id": tarif_id,
        "baslik": "Menemen",
        "aciklama": "Klasik Türk kahvaltısı",
        "malzemeler": ["domates", "biber", "soğan", "yumurta"],
        "adimlar": [
            "Soğanı kavurun",
            "Biber ve domatesi ekleyin",
            "Yumurtaları ekleyin"
        ],
        "sure": 15,
        "zorluk": "kolay"
    }


@app.post("/api/alisveris/olustur")
async def alisveris_olustur(tarif_ids: List[int], db: Session = Depends(get_db)):
    """
    Seçilen tariflerden alışveriş listesi oluştur
    
    - Tariflerdeki malzemeleri toplar
    - Evdeki malzemeleri çıkarır
    - Eksik malzeme listesi oluşturur
    """
    # TODO: Gerçek implementasyon
    return {
        "success": True,
        "eksik_malzemeler": [
            {"name": "yumurta", "miktar": 6, "birim": "adet"},
            {"name": "un", "miktar": 500, "birim": "gram"}
        ],
        "liste_id": 1
    }


@app.get("/api/ayarlar")
async def ayarlar_getir():
    """Kullanıcı ayarlarını getir"""
    return {
        "ai_mode": settings.AI_MODE,
        "ai_quota": settings.MAX_FREE_AI_REQUESTS,
        "data_sharing": True
    }


@app.post("/api/ayarlar")
async def ayarlar_guncelle(ai_mode: str):
    """Kullanıcı ayarlarını güncelle"""
    if ai_mode not in ["auto", "manual", "hybrid", "off"]:
        raise HTTPException(status_code=400, detail="Geçersiz AI modu")
    
    # TODO: Veritabanına kaydet
    return {
        "success": True,
        "ai_mode": ai_mode
    }


# Uygulama başlatma eventi
@app.on_event("startup")
async def startup_event():
    """Uygulama başlarken"""
    print("=" * 50)
    print(f"🍳 {settings.APP_NAME} başlatılıyor...")
    print(f"📊 Debug modu: {settings.DEBUG}")
    print(f"🤖 AI aktif: {ai_service.enabled}")
    print(f"⚙️  AI modu: {settings.AI_MODE}")
    print(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
