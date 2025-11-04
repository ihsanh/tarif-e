"""
Malzeme Routes - Güncellenmiş Versiyon
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Malzeme, KullaniciMalzeme
from app.schemas.malzeme import MalzemeEkle, MalzemeGuncelle
from app.services.ai_service import ai_service
import shutil
from pathlib import Path
import logging
import traceback # Hata izini loglamak için eklendi
from sqlalchemy.exc import IntegrityError # Spesifik DB hataları için

# Logger nesnesi oluşturma
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/malzeme", tags=["Malzeme"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/tani")
async def malzeme_tani(file: UploadFile = File(...)):
    """Fotoğraftan malzeme tanıma"""
    logger.info(f"Malzeme tanıma isteği alındı. Dosya: {file.filename}")

    if not ai_service.enabled:
        logger.warning("AI servisi aktif değil. Malzeme tanıma yapılamadı.")
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. GEMINI_API_KEY ayarlanmalı."
        )

    try:
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Dosya başarıyla kaydedildi: {file_path}")

        malzemeler = ai_service.malzeme_tani(str(file_path))
        logger.info(f"AI tarafından {len(malzemeler)} malzeme tanındı.")

        return {
            "success": True,
            "malzemeler": malzemeler,
            "count": len(malzemeler)
        }
    except Exception as e:
        logger.error(f"Malzeme tanıma sırasında kritik hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Malzeme tanıma sırasında bir sunucu hatası oluştu.")


@router.post("/ekle")
async def malzeme_ekle(malzeme: MalzemeEkle, db: Session = Depends(get_db)):
    """Manuel malzeme ekleme - Varsa miktarı artır"""
    user_id = 1 # Kimlik doğrulama sonrası değişecek
    logger.info(f"Kullanıcı {user_id} için malzeme ekleme/güncelleme isteği: {malzeme.name}")

    try:
        db_malzeme = db.query(Malzeme).filter(Malzeme.name == malzeme.name.lower()).first()

        if not db_malzeme:
            db_malzeme = Malzeme(name=malzeme.name.lower(), category="genel")
            db.add(db_malzeme)
            db.flush() # ID almak için commit öncesi flush
            logger.info(f"Yeni genel malzeme eklendi: {db_malzeme.name}")

        kullanici_malzeme = db.query(KullaniciMalzeme).filter(
            KullaniciMalzeme.user_id == user_id,
            KullaniciMalzeme.malzeme_id == db_malzeme.id
        ).first()

        if kullanici_malzeme:
            kullanici_malzeme.miktar += malzeme.miktar
            message = f"{malzeme.name} miktarı güncellendi ({kullanici_malzeme.miktar} {kullanici_malzeme.birim})"
            logger.info(message)
        else:
            kullanici_malzeme = KullaniciMalzeme(
                user_id=user_id,
                malzeme_id=db_malzeme.id,
                miktar=malzeme.miktar,
                birim=malzeme.birim
            )
            db.add(kullanici_malzeme)
            message = f"{malzeme.name} eklendi"
            logger.info(message)

        db.commit()
        db.refresh(kullanici_malzeme)

    except Exception as e:
        db.rollback()
        logger.error(f"Malzeme eklenirken/güncellenirken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Malzeme işlemi sırasında bir sunucu hatası oluştu.")

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
    user_id = 1 # Kimlik doğrulama sonrası değişecek
    logger.info(f"Kullanıcı {user_id} için malzeme listesi isteği.")

    try:
        user_malzemeler = db.query(KullaniciMalzeme).filter(
            KullaniciMalzeme.user_id == user_id
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

        logger.info(f"Kullanıcıya {len(malzemeler)} adet malzeme döndürüldü.")
        return {"malzemeler": malzemeler}

    except Exception as e:
        logger.error(f"Malzeme listesi alınırken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Malzeme listesi alınırken bir sunucu hatası oluştu.")


@router.put("/{malzeme_id}")
async def malzeme_guncelle(
    malzeme_id: int,
    guncelleme: MalzemeGuncelle,
    db: Session = Depends(get_db)
):
    """Malzeme miktarını güncelle"""
    user_id = 1 # Kimlik doğrulama sonrası değişecek
    logger.info(f"Kullanıcı {user_id} için malzeme ID {malzeme_id} güncelleme isteği.")

    malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.id == malzeme_id,
        KullaniciMalzeme.user_id == user_id
    ).first()

    if not malzeme:
        logger.warning(f"Malzeme ID {malzeme_id} bulunamadı.")
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")

    try:
        malzeme.miktar = guncelleme.miktar
        malzeme.birim = guncelleme.birim
        db.commit()
        logger.info(f"Malzeme ID {malzeme_id} miktarı başarıyla güncellendi: {malzeme.miktar} {malzeme.birim}")

    except Exception as e:
        db.rollback()
        logger.error(f"Malzeme güncellenirken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Malzeme güncellenirken sunucu hatası.")

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
    user_id = 1 # Kimlik doğrulama sonrası değişecek
    logger.info(f"Kullanıcı {user_id} için malzeme silme isteği: ID {malzeme_id}")

    malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.id == malzeme_id,
        KullaniciMalzeme.user_id == user_id
    ).first()

    if not malzeme:
        logger.warning(f"Malzeme ID {malzeme_id} silme isteği başarısız: Bulunamadı.")
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")

    try:
        db.delete(malzeme)
        db.commit()
        logger.info(f"Malzeme ID {malzeme_id} başarıyla silindi.")
    except Exception as e:
        db.rollback()
        logger.error(f"Malzeme silinirken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Malzeme silinirken sunucu hatası.")

    return {"success": True, "message": "Malzeme silindi"}