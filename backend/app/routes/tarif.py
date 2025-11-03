"""
Tarif Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FavoriTarif
from app.schemas.tarif import TarifOner, TarifFavori
from app.services.ai_service import ai_service
import json

router = APIRouter(prefix="/api", tags=["Tarif"])


@router.post("/tarif/oner")
async def tarif_oner(request: TarifOner):
    """Malzemelerden tarif öner"""
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


@router.post("/favoriler/ekle")
async def tarif_favori_ekle(request: TarifFavori, db: Session = Depends(get_db)):
    """Tarifi favorilere ekle"""
    tarif = request.tarif
    
    print("=" * 50)
    print("⭐ Favori ekleniyor...")
    print(f"   Tarif: {tarif.get('baslik')}")
    
    try:
        favori = FavoriTarif(
            user_id=1,
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
        
        print(f"✅ Favori eklendi, ID: {favori.id}")
        print("=" * 50)
        
        return {
            "success": True,
            "message": "Tarif favorilere eklendi",
            "favori_id": favori.id
        }
    except Exception as e:
        print(f"❌ Hata: {e}")
        print("=" * 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favoriler/liste")
async def tarif_favoriler(db: Session = Depends(get_db)):
    """Favori tarifleri listele"""
    print("=" * 50)
    print("⭐ Favoriler listeleniyor...")
    
    try:
        favoriler = db.query(FavoriTarif).filter(
            FavoriTarif.user_id == 1
        ).order_by(FavoriTarif.eklenme_tarihi.desc()).all()
        
        print(f"   Bulunan favori sayısı: {len(favoriler)}")
        
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
        
        print(f"✅ {len(result)} favori döndürülüyor")
        print("=" * 50)
        
        return {
            "success": True,
            "favoriler": result
        }
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/favoriler/{favori_id}")
async def tarif_favori_sil(favori_id: int, db: Session = Depends(get_db)):
    """Favori tarifi sil"""
    print(f"🗑️ Favori siliniyor: {favori_id}")
    
    favori = db.query(FavoriTarif).filter(
        FavoriTarif.id == favori_id,
        FavoriTarif.user_id == 1
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
