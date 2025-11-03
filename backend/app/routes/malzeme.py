"""
Malzeme Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Malzeme, KullaniciMalzeme
from app.schemas.malzeme import MalzemeEkle, MalzemeGuncelle
from app.services.ai_service import ai_service
import shutil
from pathlib import Path

router = APIRouter(prefix="/api/malzeme", tags=["Malzeme"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/tani")
async def malzeme_tani(file: UploadFile = File(...)):
    """Fotoğraftan malzeme tanıma"""
    if not ai_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. GEMINI_API_KEY ayarlanmalı."
        )
    
    try:
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        malzemeler = ai_service.malzeme_tani(str(file_path))
        
        return {
            "success": True,
            "malzemeler": malzemeler,
            "count": len(malzemeler)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ekle")
async def malzeme_ekle(malzeme: MalzemeEkle, db: Session = Depends(get_db)):
    """Manuel malzeme ekleme - Varsa miktarı artır"""
    db_malzeme = db.query(Malzeme).filter(Malzeme.name == malzeme.name.lower()).first()

    if not db_malzeme:
        db_malzeme = Malzeme(name=malzeme.name.lower(), category="genel")
        db.add(db_malzeme)
        db.commit()
        db.refresh(db_malzeme)

    kullanici_malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.user_id == 1,
        KullaniciMalzeme.malzeme_id == db_malzeme.id
    ).first()
    
    if kullanici_malzeme:
        kullanici_malzeme.miktar += malzeme.miktar
        message = f"{malzeme.name} miktarı güncellendi ({kullanici_malzeme.miktar} {kullanici_malzeme.birim})"
    else:
        kullanici_malzeme = KullaniciMalzeme(
            user_id=1,
            malzeme_id=db_malzeme.id,
            miktar=malzeme.miktar,
            birim=malzeme.birim
        )
        db.add(kullanici_malzeme)
        message = f"{malzeme.name} eklendi"
    
    db.commit()
    db.refresh(kullanici_malzeme)

    return {
        "success": True,
        "message": message,
        "malzeme": {
            "id": kullanici_malzeme.id,
            "name": db_malzeme.name,
            "miktar": kullanici_malzeme.miktar,
            "birim": kullanici_malzeme.birim
        }
    }


@router.get("/liste")
async def malzeme_liste(db: Session = Depends(get_db)):
    """Kullanıcının malzeme listesi"""
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

    return {"malzemeler": malzemeler}


@router.put("/{malzeme_id}")
async def malzeme_guncelle(
    malzeme_id: int,
    guncelleme: MalzemeGuncelle,
    db: Session = Depends(get_db)
):
    """Malzeme miktarını güncelle"""
    malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.id == malzeme_id,
        KullaniciMalzeme.user_id == 1
    ).first()
    
    if not malzeme:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")
    
    malzeme.miktar = guncelleme.miktar
    malzeme.birim = guncelleme.birim
    db.commit()
    
    return {
        "success": True,
        "message": "Malzeme güncellendi",
        "malzeme": {
            "id": malzeme.id,
            "miktar": malzeme.miktar,
            "birim": malzeme.birim
        }
    }


@router.delete("/{malzeme_id}")
async def malzeme_sil(malzeme_id: int, db: Session = Depends(get_db)):
    """Malzeme sil"""
    malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.id == malzeme_id,
        KullaniciMalzeme.user_id == 1
    ).first()

    if not malzeme:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")

    db.delete(malzeme)
    db.commit()

    return {"success": True, "message": "Malzeme silindi"}
