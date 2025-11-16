"""
Alışveriş Listesi Paylaşım Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AlisverisListesi, ListePaylasim, User, PaylaşımRolü
from app.utils.auth import get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/paylasim", tags=["Paylaşım"])


@router.post("/davet-gonder")
async def davet_gonder(
        liste_id: int = Body(...),
        paylasilan_email: str = Body(...),
        rol: str = Body("view"),  # "view" veya "edit"
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Alışveriş listesini başka bir kullanıcıyla paylaş"""
    logger.info(f"Kullanıcı {current_user.id} liste {liste_id}'yi {paylasilan_email} ile paylaşıyor")

    # Liste kontrolü - sadece sahip paylaşabilir
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == current_user.id
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı veya paylaşma yetkiniz yok")

    # Paylaşılacak kullanıcıyı bul
    paylasilan_user = db.query(User).filter(User.email == paylasilan_email.lower()).first()

    if not paylasilan_user:
        raise HTTPException(status_code=404, detail="Bu email adresiyle kayıtlı kullanıcı bulunamadı")

    # Kendisiyle paylaşmayı engelle
    if paylasilan_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Listeyi kendinizle paylaşamazsınız")

    # Zaten paylaşılmış mı kontrol et
    mevcut_paylasim = db.query(ListePaylasim).filter(
        ListePaylasim.liste_id == liste_id,
        ListePaylasim.paylasilan_user_id == paylasilan_user.id
    ).first()

    if mevcut_paylasim:
        raise HTTPException(status_code=400, detail="Bu liste zaten bu kullanıcıyla paylaşılmış")

    # Rol kontrolü
    if rol not in ["view", "edit"]:
        rol = "view"

    rol_enum = PaylaşımRolü.GORUNTULEYEBILIR if rol == "view" else PaylaşımRolü.DUZENLEYEBILIR

    # Paylaşım kaydı oluştur
    paylasim = ListePaylasim(
        liste_id=liste_id,
        paylasan_user_id=current_user.id,
        paylasilan_user_id=paylasilan_user.id,
        rol=rol_enum,
        kabul_edildi=False  # Kullanıcı onayı bekliyor
    )

    db.add(paylasim)
    db.commit()

    logger.info(f"Davet başarıyla gönderildi: {paylasilan_user.username}")

    return {
        "success": True,
        "message": f"Davet {paylasilan_user.username} kullanıcısına gönderildi",
        "paylasim_id": paylasim.id
    }


@router.get("/davetler")
async def davetleri_getir(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Kullanıcının aldığı bekleyen davetleri getir"""
    davetler = db.query(ListePaylasim).filter(
        ListePaylasim.paylasilan_user_id == current_user.id,
        ListePaylasim.kabul_edildi == False
    ).all()

    result = []
    for davet in davetler:
        paylasan = db.query(User).filter(User.id == davet.paylasan_user_id).first()
        liste = db.query(AlisverisListesi).filter(AlisverisListesi.id == davet.liste_id).first()

        if paylasan and liste:
            result.append({
                "id": davet.id,
                "liste_id": liste.id,
                "liste_baslik": liste.baslik,
                "paylasan_kullanici": paylasan.username,
                "paylasan_email": paylasan.email,
                "rol": "Görüntüleme" if davet.rol == PaylaşımRolü.GORUNTULEYEBILIR else "Düzenleme",
                "tarih": davet.paylasim_tarihi.isoformat()
            })

    return {
        "success": True,
        "davetler": result
    }


@router.post("/davet-kabul/{davet_id}")
async def davet_kabul(
        davet_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Daveti kabul et"""
    davet = db.query(ListePaylasim).filter(
        ListePaylasim.id == davet_id,
        ListePaylasim.paylasilan_user_id == current_user.id
    ).first()

    if not davet:
        raise HTTPException(status_code=404, detail="Davet bulunamadı")

    davet.kabul_edildi = True
    db.commit()

    logger.info(f"Kullanıcı {current_user.id} daveti {davet_id} kabul etti")

    return {
        "success": True,
        "message": "Davet kabul edildi"
    }


@router.delete("/davet-reddet/{davet_id}")
async def davet_reddet(
        davet_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Daveti reddet"""
    davet = db.query(ListePaylasim).filter(
        ListePaylasim.id == davet_id,
        ListePaylasim.paylasilan_user_id == current_user.id
    ).first()

    if not davet:
        raise HTTPException(status_code=404, detail="Davet bulunamadı")

    db.delete(davet)
    db.commit()

    logger.info(f"Kullanıcı {current_user.id} daveti {davet_id} reddetti")

    return {
        "success": True,
        "message": "Davet reddedildi"
    }


@router.get("/liste/{liste_id}/paylasilanlar")
async def liste_paylasilanlar(
        liste_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Listenin kimlerle paylaşıldığını getir"""
    # Liste kontrolü
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == current_user.id
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    paylasimlar = db.query(ListePaylasim).filter(
        ListePaylasim.liste_id == liste_id
    ).all()

    result = []
    for paylasim in paylasimlar:
        paylasilan = db.query(User).filter(User.id == paylasim.paylasilan_user_id).first()

        if paylasilan:
            result.append({
                "id": paylasim.id,
                "kullanici": paylasilan.username,
                "email": paylasilan.email,
                "rol": "Görüntüleme" if paylasim.rol == PaylaşımRolü.GORUNTULEYEBILIR else "Düzenleme",
                "durum": "Kabul Edildi" if paylasim.kabul_edildi else "Bekliyor",
                "tarih": paylasim.paylasim_tarihi.isoformat()
            })

    return {
        "success": True,
        "paylasilanlar": result
    }


@router.delete("/paylasilandan-cikar/{paylasim_id}")
async def paylasilandan_cikar(
        paylasim_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Paylaşımı iptal et (sadece liste sahibi)"""
    paylasim = db.query(ListePaylasim).filter(
        ListePaylasim.id == paylasim_id
    ).first()

    if not paylasim:
        raise HTTPException(status_code=404, detail="Paylaşım bulunamadı")

    # Liste sahibi mi kontrol et
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == paylasim.liste_id,
        AlisverisListesi.user_id == current_user.id
    ).first()

    if not liste:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")

    db.delete(paylasim)
    db.commit()

    return {
        "success": True,
        "message": "Paylaşım iptal edildi"
    }


@router.get("/benimle-paylasilanlar")
async def benimle_paylasilanlar(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Benimle paylaşılan listeleri getir"""
    paylasimlar = db.query(ListePaylasim).filter(
        ListePaylasim.paylasilan_user_id == current_user.id,
        ListePaylasim.kabul_edildi == True
    ).all()

    result = []
    for paylasim in paylasimlar:
        liste = db.query(AlisverisListesi).filter(
            AlisverisListesi.id == paylasim.liste_id
        ).first()

        paylasan = db.query(User).filter(
            User.id == paylasim.paylasan_user_id
        ).first()

        if liste and paylasan:
            result.append({
                "id": liste.id,
                "baslik": liste.baslik,
                "aciklama": liste.aciklama,
                "paylasan": paylasan.username,
                "rol": "Görüntüleme" if paylasim.rol == PaylaşımRolü.GORUNTULEYEBILIR else "Düzenleme",
                "olusturma_tarihi": liste.olusturma_tarihi.isoformat(),
                "tamamlandi": liste.tamamlandi
            })

    return {
        "success": True,
        "listeler": result
    }