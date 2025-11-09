"""
Tarif Routes - Güncellenmiş Versiyon
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FavoriTarif
from app.schemas.tarif import TarifOner, TarifFavori
from app.services.ai_service import ai_service
import json
import logging
import traceback
from sqlalchemy.exc import IntegrityError
from app.utils.auth import get_current_user
from app.models import User

# Logger nesnesi oluşturma
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Tarif"])


@router.post("/tarif/oner")
async def tarif_oner(request: TarifOner,current_user: User = Depends(get_current_user)):
    """Malzemelerden tarif öner"""
    logger.info(f"Kullanıcı {current_user.id} önerme isteği alındı.")


    if not ai_service.enabled:
        logger.warning("AI servisi aktif değil.")
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. Manuel tarif ekleyin."
        )

    try:
        preferences = {}
        # İstek body'sindeki tercihler alınır
        if request.sure:
            preferences['sure'] = request.sure
        if request.zorluk:
            preferences['zorluk'] = request.zorluk
        if request.kategori:
            preferences['kategori'] = request.kategori

        # Eğer ai_service.tarif_oner asenkron ise await kullanın
        tarif = ai_service.tarif_oner(request.malzemeler, preferences)

        logger.info(f"AI tarafından başarıyla tarif önerildi.")

        return {
            "success": True,
            "tarif": tarif
        }
    except Exception as e:
        # Hata izini loglama
        logger.error(f"Tarif önerme sırasında beklenmedik hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Tarif önerilirken bir sunucu hatası oluştu.")


@router.post("/favoriler/ekle")
async def tarif_favori_ekle(request: TarifFavori,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tarifi favorilere ekle"""
    tarif = request.tarif
    user_id = current_user.id

    logger.info(f"Kullanıcı ID {user_id} için favori tarif ekleniyor: {tarif.get('baslik')}")

    try:
        favori = FavoriTarif(
            user_id=user_id,
            baslik=tarif.get('baslik', 'İsimsiz Tarif'),
            aciklama=tarif.get('aciklama'),
            # JSON olarak saklama işlemi
            malzemeler=json.dumps(tarif.get('malzemeler', []), ensure_ascii=False),
            adimlar=json.dumps(tarif.get('adimlar', []), ensure_ascii=False),
            sure=tarif.get('sure'),
            zorluk=tarif.get('zorluk'),
            kategori=tarif.get('kategori')
        )

        db.add(favori)
        db.commit()
        db.refresh(favori)

        logger.info(f"Favori tarif başarıyla eklendi, ID: {favori.id}")

        return {
            "success": True,
            "message": "Tarif favorilere eklendi",
            "favori_id": favori.id
        }
    except IntegrityError:
        # Tekrarlanan giriş gibi veritabanı kısıtlaması hatası
        logger.warning(f"Kullanıcı {user_id} için veritabanı bütünlüğü hatası (IntegrityError).")
        db.rollback()
        raise HTTPException(status_code=400, detail="Bu tarif zaten favorilerinizde olabilir.")
    except Exception as e:
        logger.error(f"Favori eklenirken hata: {e}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Favori eklenirken bir sunucu hatası oluştu.")


@router.get("/favoriler/liste")
async def tarif_favoriler(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Favori tarifleri listele"""
    user_id = current_user.id

    logger.info(f"Kullanıcı {user_id} Favori listeleme  isteği")

    try:
        # GEÇICI: user_id filtresi olmadan
        favoriler = db.query(FavoriTarif).order_by(
            FavoriTarif.eklenme_tarihi.desc()
        ).all()

        logger.info(f"Toplam {len(favoriler)} adet favori bulundu.")

        result = []
        for fav in favoriler:
            result.append({
                "id": fav.id,
                "baslik": fav.baslik,
                "aciklama": fav.aciklama,
                "malzemeler": json.loads(fav.malzemeler) if fav.malzemeler else [],
                "adimlar": json.loads(fav.adimlar) if fav.adimlar else [],
                "sure": fav.sure,
                "zorluk": fav.zorluk,
                "kategori": fav.kategori,
                "eklenme_tarihi": fav.eklenme_tarihi.isoformat()
            })

        logger.info(f"{len(result)} favori döndürülüyor.")

        return {
            "success": True,
            "favoriler": result
        }
    except Exception as e:
        logger.error(f"Favori listelenirken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Favori listesi alınırken bir sunucu hatası oluştu.")


@router.get("/favoriler/{favori_id}")
async def tarif_favori_detay(favori_id: int ,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Favori tarif detayını getir"""
    user_id = current_user.id

    logger.info(f"Kullanıcı {user_id} Favori detay isteği: ID {favori_id}")

    try:
        # GEÇICI: user_id filtresi olmadan
        favori = db.query(FavoriTarif).filter(
            FavoriTarif.id == favori_id
        ).first()

        if not favori:
            logger.warning(f"Favori ID {favori_id} veritabanında bulunamadı.")
            raise HTTPException(status_code=404, detail="Favori bulunamadı")

        # DEBUG: User ID'yi logla
        logger.info(f"Favori bulundu! ID: {favori.id}, User ID: {favori.user_id}")

        result = {
            "id": favori.id,
            "baslik": favori.baslik,
            "aciklama": favori.aciklama,
            "malzemeler": json.loads(favori.malzemeler) if favori.malzemeler else [],
            "adimlar": json.loads(favori.adimlar) if favori.adimlar else [],
            "sure": favori.sure,
            "zorluk": favori.zorluk,
            "kategori": favori.kategori,
            "eklenme_tarihi": favori.eklenme_tarihi.isoformat()
        }

        logger.info(f"Favori detayı döndürülüyor: {favori.baslik}")

        return {
            "success": True,
            "favori": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Favori detay alınırken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Favori detayı alınırken bir sunucu hatası oluştu.")


@router.delete("/favoriler/{favori_id}")
async def tarif_favori_sil(favori_id: int ,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Favori tarifi sil"""
    user_id = current_user.id
    logger.info(f"Kullanıcı {user_id} için Favori silme isteği: ID {favori_id}")

    favori = db.query(FavoriTarif).filter(
        FavoriTarif.id == favori_id,
        FavoriTarif.user_id == user_id
    ).first()

    if not favori:
        raise HTTPException(status_code=404, detail="Favori bulunamadı")

    db.delete(favori)
    db.commit()

    print(f"✅ Favori silindi")

    return {
        "success": True,
        "message": "Favori silindi"
    }

