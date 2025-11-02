"""
Tarif-e FastAPI Ana Uygulama
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import shutil
import os
from pathlib import Path

from .config import settings
from .database import engine, Base, get_db, init_db
from .services.ai_service import ai_service

print("🔥 MAIN.PY YÜKLENDI! 🔥")

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# Pydantic models
class MalzemeEkle(BaseModel):
    name: str
    miktar: Optional[float] = 1.0
    birim: Optional[str] = "adet"

class TarifOner(BaseModel):
    malzemeler: List[str]
    sure: Optional[int] = None
    zorluk: Optional[str] = None
    kategori: Optional[str] = None

class AlisverisRequest(BaseModel):
    malzemeler: List[str]


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
    """
    from .database import Malzeme, KullaniciMalzeme

    # Malzeme var mı kontrol et
    db_malzeme = db.query(Malzeme).filter(Malzeme.name == malzeme.name.lower()).first()

    # Yoksa oluştur
    if not db_malzeme:
        db_malzeme = Malzeme(
            name=malzeme.name.lower(),
            category="genel"
        )
        db.add(db_malzeme)
        db.commit()
        db.refresh(db_malzeme)

    # Kullanıcı malzemesini ekle (şimdilik user_id=1 sabit)
    kullanici_malzeme = KullaniciMalzeme(
        user_id=1,  # TODO: Gerçek user authentication
        malzeme_id=db_malzeme.id,
        miktar=malzeme.miktar,
        birim=malzeme.birim
    )
    db.add(kullanici_malzeme)
    db.commit()

    return {
        "success": True,
        "message": f"{malzeme.name} eklendi",
        "malzeme": {
            "id": db_malzeme.id,
            "name": db_malzeme.name,
            "miktar": malzeme.miktar,
            "birim": malzeme.birim
        }
    }


@app.get("/api/malzeme/liste")
async def malzeme_liste(db: Session = Depends(get_db)):
    """
    Kullanıcının malzeme listesi
    """
    from .database import KullaniciMalzeme, Malzeme

    # Kullanıcının malzemelerini çek (şimdilik user_id=1)
    user_malzemeler = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.user_id == 1
    ).all()

    malzemeler = []
    for um in user_malzemeler:
        malzeme = db.query(Malzeme).filter(Malzeme.id == um.malzeme_id).first()
        if malzeme:
            malzemeler.append({
                "id": um.id,
                "name": malzeme.name,
                "miktar": um.miktar,
                "birim": um.birim,
                "eklenme_tarihi": um.eklenme_tarihi.isoformat() if um.eklenme_tarihi else None
            })

    return {
        "malzemeler": malzemeler
    }


@app.delete("/api/malzeme/{malzeme_id}")
async def malzeme_sil(malzeme_id: int, db: Session = Depends(get_db)):
    """
    Malzeme sil
    """
    from .database import KullaniciMalzeme

    malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.id == malzeme_id,
        KullaniciMalzeme.user_id == 1  # TODO: Gerçek user
    ).first()

    if not malzeme:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")

    db.delete(malzeme)
    db.commit()

    return {"success": True, "message": "Malzeme silindi"}


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
async def alisveris_olustur(request: dict, db: Session = Depends(get_db)):
    print("🔥 alışveris YÜKLENDI! 🔥")

    """
    Tarifteki malzemelerden alışveriş listesi oluştur
    """
    from .database import AlisverisListesi, AlisverisUrunu, Malzeme, KullaniciMalzeme

    print("=" * 50)
    print("🛒 Alışveriş listesi oluşturuluyor...")
    print(f"📦 Gelen request: {request}")

    try:
        # dict'ten malzemeleri çıkar
        tarif_malzemeleri = request.get("malzemeler", [])
        print(f"📋 Malzemeler: {tarif_malzemeleri}")

        if not tarif_malzemeleri:
            return {"success": False, "message": "Malzeme listesi boş"}

        # Kullanıcının mevcut malzemelerini al
        user_malzemeler = db.query(KullaniciMalzeme).filter(
            KullaniciMalzeme.user_id == 1
        ).all()

        user_malzeme_dict = {}
        for um in user_malzemeler:
            malzeme = db.query(Malzeme).filter(Malzeme.id == um.malzeme_id).first()
            if malzeme:
                user_malzeme_dict[malzeme.name.lower()] = um.miktar

        print(f"🏠 Evdeki malzemeler: {list(user_malzeme_dict.keys())}")

        # Eksik malzemeleri bul
        eksik_malzemeler = []

        for item in tarif_malzemeleri:
            print(f"   İşleniyor: {item}")
            parts = item.split('-')
            if len(parts) >= 2:
                malzeme_adi = parts[0].strip().lower()
                miktar_birim = parts[1].strip()

                miktar_parts = miktar_birim.split()
                try:
                    miktar = float(miktar_parts[0]) if miktar_parts else 1
                    birim = miktar_parts[1] if len(miktar_parts) > 1 else "adet"
                except:
                    miktar = 1
                    birim = "adet"

                if malzeme_adi not in user_malzeme_dict:
                    eksik_malzemeler.append({
                        "name": malzeme_adi,
                        "miktar": miktar,
                        "birim": birim
                    })
                    print(f"      ❌ Eksik: {malzeme_adi}")
                else:
                    print(f"      ✅ Var: {malzeme_adi}")

        print(f"📝 Toplam eksik: {len(eksik_malzemeler)}")

        # Liste oluştur
        alisveris_listesi = AlisverisListesi(
            user_id=1,
            durum="aktif",
            notlar=f"{len(eksik_malzemeler)} eksik malzeme"
        )
        db.add(alisveris_listesi)
        db.commit()
        db.refresh(alisveris_listesi)

        print(f"✅ Liste ID: {alisveris_listesi.id}")

        # Ürünleri ekle
        for item in eksik_malzemeler:
            malzeme = db.query(Malzeme).filter(Malzeme.name == item["name"]).first()

            if not malzeme:
                malzeme = Malzeme(name=item["name"], category="genel")
                db.add(malzeme)
                db.commit()
                db.refresh(malzeme)

            alisveris_urunu = AlisverisUrunu(
                liste_id=alisveris_listesi.id,
                malzeme_id=malzeme.id,
                miktar=item["miktar"],
                birim=item["birim"],
                alinma_durumu=False
            )
            db.add(alisveris_urunu)

        db.commit()
        print("✅ Başarılı!")
        print("=" * 50)

        return {
            "success": True,
            "eksik_malzemeler": eksik_malzemeler,
            "liste_id": alisveris_listesi.id,
            "message": f"{len(eksik_malzemeler)} eksik malzeme"
        }

    except Exception as e:
        print(f"❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return {"success": False, "message": str(e)}

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