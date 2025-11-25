"""
Tarif Routes - Profil Tercihleri ile Güncellenmiş
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FavoriTarif
from app.models.user_profile import UserProfile
from app.schemas.tarif import TarifOner, TarifFavori
from app.services.ai_service import ai_service
import json
import logging
import traceback
from sqlalchemy.exc import IntegrityError
from app.utils.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Tarif"])


@router.post("/tarif/oner")
async def tarif_oner(request: TarifOner, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Malzemelerden tarif öner - Kullanıcı tercihleri dahil"""
    logger.info(f"Kullanıcı {current_user.id} önerme isteği alındı.")

    if not ai_service.enabled:
        logger.warning("AI servisi aktif değil.")
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. Manuel tarif ekleyin."
        )

    try:
        # Kullanıcı profil tercihlerini getir
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

        preferences = {}

        # İstek body'sindeki tercihler alınır
        if request.sure:
            preferences['sure'] = request.sure
        if request.zorluk:
            preferences['zorluk'] = request.zorluk
        if request.kategori:
            preferences['kategori'] = request.kategori

        # Profil tercihlerini ekle
        if profile:
            if profile.dietary_preferences:
                preferences['dietary_preferences'] = profile.dietary_preferences
                logger.info(f"Diyet tercihleri: {profile.dietary_preferences}")

            if profile.allergies:
                preferences['allergies'] = profile.allergies
                logger.info(f"Alerjiler: {profile.allergies}")

            if profile.dislikes:
                preferences['dislikes'] = profile.dislikes
                logger.info(f"Sevmediği yiyecekler: {profile.dislikes}")

        # AI'dan tarif iste
        tarif = ai_service.tarif_oner(request.malzemeler, preferences)

        logger.info(f"AI tarafından başarıyla tarif önerildi.")

        return {
            "success": True,
            "tarif": tarif
        }
    except Exception as e:
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
        favori = db.query(FavoriTarif).filter(
            FavoriTarif.id == favori_id
        ).first()

        if not favori:
            logger.warning(f"Favori ID {favori_id} veritabanında bulunamadı.")
            raise HTTPException(status_code=404, detail="Favori bulunamadı")

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
