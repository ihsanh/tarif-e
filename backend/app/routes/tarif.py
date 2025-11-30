"""
Tarif Routes - Profil Tercihleri ile Güncellenmiş
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
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

class NutritionRequest(BaseModel):
    """Besin değerleri hesaplama request"""
    baslik: str
    malzemeler: List[str]
    porsiyon: int = 4


class NutritionResponse(BaseModel):
    """Besin değerleri response"""
    success: bool
    message: str
    nutrition: dict

@router.post("/tarif/nutrition", response_model=NutritionResponse)
async def calculate_nutrition(
        request: NutritionRequest,
        current_user: User = Depends(get_current_user)
):
    """Tarif için besin değerlerini hesapla"""
    try:
        logger.info(f"Besin değerleri: {request.baslik}")

        # AI ile hesapla
        nutrition_data = await ai_service.calculate_nutrition(
            recipe_title=request.baslik,
            ingredients=request.malzemeler,
            portions=request.porsiyon
        )

        return NutritionResponse(
            success=True,
            message="Besin değerleri hesaplandı",
            nutrition=nutrition_data
        )

    except Exception as e:
        logger.error(f"Nutrition error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Besin değerleri hesaplanamadı: {str(e)}"
        )

# ============================================
# OPSIYONEL: Test endpoint'i
# ============================================

@router.get("/tarif/nutrition/test")
async def test_nutrition(current_user: User = Depends(get_current_user)):
    """
    Besin değerleri hesaplama test endpoint
    Geliştirme sırasında kullanılır
    """
    test_recipe = {
        "baslik": "Test Menemen",
        "malzemeler": [
            "3 adet yumurta",
            "2 adet domates",
            "1 adet biber",
            "1 adet soğan",
            "2 yemek kaşığı tereyağı"
        ],
        "porsiyon": 2
    }

    nutrition = await ai_service.calculate_nutrition(
        recipe_title=test_recipe["baslik"],
        ingredients=test_recipe["malzemeler"],
        portions=test_recipe["porsiyon"]
    )

    return {
        "success": True,
        "test_recipe": test_recipe,
        "nutrition": nutrition
    }
