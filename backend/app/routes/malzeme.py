"""
Malzeme Routes - Güncellenmiş Versiyon
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.malzeme import MalzemeEkle, MalzemeGuncelle
from app.services.ai_service import ai_service
import shutil
from pathlib import Path
import logging
import traceback
from app.utils.auth import get_current_user
from app.models import User
from app.models import Malzeme, MalzemeKategorisi


# Logger nesnesi oluşturma
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/malzeme", tags=["Malzeme"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/tani")
async def malzeme_tani(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Fotoğraftan malzeme tanıma"""
    logger.info(f"Kullanıcı {current_user.id} malzeme tanıma isteği yaptı")

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
async def malzeme_ekle(
        malzeme: MalzemeEkle,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Manuel malzeme ekleme - Varsa miktarı artır

    BASİT MANTIK:
    1. Kullanıcının bu malzemesi var mı kontrol et
    2. Varsa → Miktarı artır
    3. Yoksa → Yeni ekle
    """
    logger.info(f"Kullanıcı {current_user.id} için malzeme ekleme: {malzeme.name}")

    try:
        # Kullanıcının bu malzemesi var mı?
        kullanici_malzeme = db.query(Malzeme).filter(
            Malzeme.name == malzeme.name.lower(),
            Malzeme.user_id == current_user.id
        ).first()

        if kullanici_malzeme:
            # ✅ VAR - Miktarı artır
            eski_miktar = kullanici_malzeme.miktar
            kullanici_malzeme.miktar += malzeme.miktar

            # Kategori güncelle (varsa)
            if hasattr(malzeme, 'kategori') and malzeme.kategori:
                kullanici_malzeme.kategori = malzeme.kategori

            message = f"{malzeme.name} miktarı güncellendi ({eski_miktar} → {kullanici_malzeme.miktar} {kullanici_malzeme.birim})"
            logger.info(message)
        else:
            # ❌ YOK - Yeni ekle
            kullanici_malzeme = Malzeme(
                name=malzeme.name.lower(),
                miktar=malzeme.miktar,
                birim=malzeme.birim,
                kategori=malzeme.kategori if hasattr(malzeme, 'kategori') else MalzemeKategorisi.DIGER,
                user_id=current_user.id
            )
            db.add(kullanici_malzeme)
            message = f"{malzeme.name} eklendi"
            logger.info(message)

        db.commit()
        db.refresh(kullanici_malzeme)

        return {
            "success": True,
            "message": message,
            "malzeme": {
                "id": kullanici_malzeme.id,
                "name": kullanici_malzeme.name,
                "miktar": kullanici_malzeme.miktar,
                "birim": kullanici_malzeme.birim,
                "kategori": kullanici_malzeme.kategori.value if kullanici_malzeme.kategori else "diğer"
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Malzeme eklenirken/güncellenirken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Malzeme işlemi sırasında hata: {str(e)}"
        )


@router.get("/liste")
async def malzeme_liste(current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """Kullanıcının malzeme listesi"""
    user_id = current_user.id
    logger.info(f"Kullanıcı {user_id} için malzeme listesi isteği.")

    try:
        malzemeler = db.query(Malzeme).filter(
            Malzeme.user_id == user_id
        ).order_by(Malzeme.name).all()

        return {
            "success": True,
            "malzemeler": [
                {
                    "id": m.id,
                    "name": m.name,
                    "miktar": m.miktar,
                    "birim": m.birim,
                    "kategori": m.kategori.value if m.kategori else "diğer"
                }
                for m in malzemeler
            ]
        }

        logger.info(f"Kullanıcıya {len(malzemeler)} adet malzeme döndürüldü.")
        return {"malzemeler": malzemeler}

    except Exception as e:
        logger.error(f"Malzeme listesi alınırken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Malzeme listesi alınırken bir sunucu hatası oluştu.")


@router.put("/{malzeme_id}")
async def malzeme_guncelle(
    malzeme_id: int,
    guncelleme: MalzemeGuncelle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Malzeme miktarını güncelle"""
    user_id = current_user.id
    logger.info(f"Kullanıcı {user_id} için malzeme ID {malzeme_id} güncelleme isteği.")

    malzeme = db.query(Malzeme).filter(
        Malzeme.id == malzeme_id,
        Malzeme.user_id == user_id
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
async def malzeme_sil(malzeme_id: int,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Malzeme sil"""
    user_id = current_user.id
    logger.info(f"Kullanıcı {user_id} için malzeme silme isteği: ID {malzeme_id}")

    malzeme = db.query(Malzeme).filter(
        Malzeme.id == malzeme_id,
        Malzeme.user_id == user_id
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