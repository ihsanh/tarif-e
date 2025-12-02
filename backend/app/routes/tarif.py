"""
Tarif Routes - Güncellenmiş ve Genişletilmiş
backend/app/routes/tarif.py
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FavoriTarif, User
from app.models.user_profile import UserProfile
from app.schemas.tarif import TarifOner, TarifFavori
from app.services.ai_service import ai_service
import json
import logging
import traceback
from sqlalchemy.exc import IntegrityError
from app.utils.auth import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Tarif"])


# ============================================
# TARİF ÖNERME
# ============================================

@router.post("/tarif/oner")
async def tarif_oner(
    request: TarifOner,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Malzemelerden tarif öner - Kullanıcı tercihleri dahil"""
    logger.info(f"Kullanıcı {current_user.id} önerme isteği aldı.")

    if not ai_service.enabled:
        logger.warning("AI servisi aktif değil.")
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. Manuel tarif ekleyin."
        )

    try:
        # Kullanıcı profil tercihlerini getir
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

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
        logger.error(f"Tarif önerme sırasında hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Tarif önerilirken bir sunucu hatası oluştu."
        )


# ============================================
# FAVORİ İŞLEMLERİ
# ============================================

@router.post("/favoriler/ekle")
async def tarif_favori_ekle(
    request: TarifFavori,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        logger.warning(f"Kullanıcı {user_id} için veritabanı bütünlüğü hatası.")
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Bu tarif zaten favorilerinizde olabilir."
        )
    except Exception as e:
        logger.error(f"Favori eklenirken hata: {e}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Favori eklenirken bir sunucu hatası oluştu."
        )


@router.get("/favoriler/liste")
async def tarif_favoriler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Favori tarifleri listele"""
    user_id = current_user.id

    logger.info(f"Kullanıcı {user_id} Favori listeleme isteği")

    try:
        # Kullanıcının favorilerini getir
        favoriler = db.query(FavoriTarif).filter(
            FavoriTarif.user_id == user_id
        ).order_by(
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
        raise HTTPException(
            status_code=500,
            detail="Favori listesi alınırken bir sunucu hatası oluştu."
        )


@router.get("/favoriler/{favori_id}")
async def tarif_favori_detay(
    favori_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Favori tarif detayını getir"""
    user_id = current_user.id

    logger.info(f"Kullanıcı {user_id} Favori detay isteği: ID {favori_id}")

    try:
        favori = db.query(FavoriTarif).filter(
            FavoriTarif.id == favori_id,
            FavoriTarif.user_id == user_id
        ).first()

        if not favori:
            logger.warning(f"Favori ID {favori_id} bulunamadı veya kullanıcıya ait değil.")
            raise HTTPException(status_code=404, detail="Favori bulunamadı")

        logger.info(f"Favori bulundu! ID: {favori.id}")

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
        raise HTTPException(
            status_code=500,
            detail="Favori detayı alınırken bir sunucu hatası oluştu."
        )


@router.delete("/favoriler/{favori_id}")
async def tarif_favori_sil(
    favori_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Favori tarifi sil"""
    user_id = current_user.id
    logger.info(f"Kullanıcı {user_id} için Favori silme isteği: ID {favori_id}")

    try:
        favori = db.query(FavoriTarif).filter(
            FavoriTarif.id == favori_id,
            FavoriTarif.user_id == user_id
        ).first()

        if not favori:
            raise HTTPException(status_code=404, detail="Favori bulunamadı")

        db.delete(favori)
        db.commit()

        logger.info(f"✅ Favori silindi: ID {favori_id}")

        return {
            "success": True,
            "message": "Favori silindi"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Favori silinirken hata: {e}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Favori silinirken bir sunucu hatası oluştu."
        )


# ============================================
# BESİN DEĞERLERİ
# ============================================

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
        logger.info(f"Besin değerleri hesaplanıyor: {request.baslik}")

        # AI ile hesapla
        nutrition_data = await ai_service.calculate_nutrition(
            recipe_title=request.baslik,
            ingredients=request.malzemeler,
            portions=request.porsiyon
        )

        logger.info(f"✅ Besin değerleri hesaplandı: {request.baslik}")

        return NutritionResponse(
            success=True,
            message="Besin değerleri hesaplandı",
            nutrition=nutrition_data
        )

    except Exception as e:
        logger.error(f"❌ Nutrition error: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Besin değerleri hesaplanamadı: {str(e)}"
        )


@router.get("/tarif/nutrition/test")
async def test_nutrition(current_user: User = Depends(get_current_user)):
    """Besin değerleri test endpoint (Development)"""
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


# ============================================
# GELİŞMİŞ FİLTRE
# ============================================

class FilterRange(BaseModel):
    """Range filter (min-max)"""
    min: int
    max: int


class FilterRequest(BaseModel):
    """Gelişmiş filtre request"""
    malzemeler: Optional[List[str]] = []
    sure: Optional[FilterRange] = None
    zorluk: Optional[List[str]] = []
    porsiyon: Optional[FilterRange] = None
    kalori: Optional[FilterRange] = None


class FilterResponse(BaseModel):
    """Filtre response"""
    success: bool
    message: str
    favoriler: List[dict]
    total: int


@router.post("/tarif/favoriler/filtrele", response_model=FilterResponse)
async def filter_favoriler(
    filters: FilterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Favorileri gelişmiş filtrelerle sorgula

    Filtreler:
    - malzemeler: İçermesi gereken malzemeler
    - sure: Min-Max süre aralığı (dakika)
    - zorluk: Zorluk seviyeleri (kolay, orta, zor)
    - porsiyon: Min-Max porsiyon aralığı
    - kalori: Min-Max kalori aralığı
    """
    try:
        logger.info(f"🔍 Filtre uygulanıyor - User: {current_user.username}")

        # Kullanıcının tüm favorilerini al
        query = db.query(FavoriTarif).filter(FavoriTarif.user_id == current_user.id)
        favoriler = query.all()

        logger.error(f"Toplam favori: {len(favoriler)}")



        # Filtreleme
        filtered_favoriler = []

        for favori in favoriler:
            # Malzemeleri parse et
            if isinstance(favori.malzemeler, str):
                favori_malzemeler = json.loads(favori.malzemeler)
            else:
                favori_malzemeler = favori.malzemeler

            # 1. Malzeme filtresi
            if filters.malzemeler and len(filters.malzemeler) > 0:
                malzeme_match = all(
                    any(
                        filter_mal.lower() in tarif_mal.lower()
                        for tarif_mal in favori_malzemeler
                    )
                    for filter_mal in filters.malzemeler
                )

                if not malzeme_match:
                    continue

            logger.error(f"filters3: {filters.sure}")
            # 2. Süre filtresi
            if filters.sure:
                try:
                    sure_str = favori.sure or "0"
                    sure_value = int(''.join(filter(str.isdigit, sure_str)))

                    if not (filters.sure.min <= sure_value <= filters.sure.max):
                        continue
                except:
                    pass



            # 3. Zorluk filtresi
            if filters.zorluk and len(filters.zorluk) > 0:
                logger.error(f"🔍 {favori.baslik} - Zorluk DB: '{favori.zorluk}'")
                logger.error(f"   Aranan: {filters.zorluk}")

                if favori.zorluk:
                    favori_zorluk = favori.zorluk.strip().lower()
                    filter_zorluklar = [z.strip().lower() for z in filters.zorluk]

                    logger.error(f"   '{favori_zorluk}' in {filter_zorluklar}?")

                    if favori_zorluk not in filter_zorluklar:
                        logger.error(f"   ❌ Uyuşmadı")
                        continue
                    logger.error(f"   ✅ Uyuştu!")

            # Tüm filtreleri geçti
            filtered_favoriler.append(favori)

        # Sonuçları dict'e çevir
        result_favoriler = []
        for favori in filtered_favoriler:
            result_favoriler.append({
                "id": favori.id,
                "baslik": favori.baslik,
                "aciklama": favori.aciklama,
                "malzemeler": json.loads(favori.malzemeler) if isinstance(favori.malzemeler, str) else favori.malzemeler,
                "adimlar": json.loads(favori.adimlar) if isinstance(favori.adimlar, str) else favori.adimlar,
                "sure": favori.sure,
                "zorluk": favori.zorluk,
                "kategori": favori.kategori,
                "eklenme_tarihi": favori.eklenme_tarihi.isoformat() if favori.eklenme_tarihi else None
            })

        logger.info(f"✅ Filtreleme tamamlandı - {len(result_favoriler)} sonuç")

        return FilterResponse(
            success=True,
            message=f"{len(result_favoriler)} tarif bulundu",
            favoriler=result_favoriler,
            total=len(result_favoriler)
        )

    except Exception as e:
        logger.error(f"❌ Filtre hatası: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Filtreleme sırasında hata oluştu: {str(e)}"
        )