"""
Alışveriş Routes - Güncellenmiş Versiyon
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AlisverisListesi, AlisverisUrunu, Malzeme, KullaniciMalzeme
from app.schemas.alisveris import AlisverisListesiCreate
import logging
import traceback
from app.utils.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

# Router tanımı
router = APIRouter(prefix="/api/alisveris", tags=["Alışveriş"])


@router.post("/olustur")
async def alisveris_olustur(request: AlisverisListesiCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tarifteki malzemelerden alışveriş listesi oluştur"""
    user_id = current_user.id # Kimlik doğrulama sonrası güncellenecek
    logger.info(f"Kullanıcı {user_id} için alışveriş listesi oluşturuluyor.")
    logger.debug(f"Gelen malzemeler: {request.malzemeler}")

    tarif_malzemeleri = request.malzemeler

    if not tarif_malzemeleri:
        logger.warning("Alışveriş listesi oluşturma: Malzeme listesi boş geldi.")
        raise HTTPException(status_code=400, detail="Malzeme listesi boş")
    try:

        user_malzemeler = db.query(KullaniciMalzeme).filter(
            KullaniciMalzeme.user_id == user_id
        ).all()

        user_malzeme_dict = {}
        for um in user_malzemeler:
            malzeme = db.query(Malzeme).filter(Malzeme.id == um.malzeme_id).first()
            if malzeme:
                # Malzeme adı veritabanında olduğu gibi (lower() olmadan) kullanılmalıdır
                user_malzeme_dict[malzeme.name.lower()] = um.miktar

        logger.info(f"Evdeki {len(user_malzeme_dict)} malzeme kontrol ediliyor.")

        eksik_malzemeler = []

        for item in tarif_malzemeleri:
            # Buradaki veri ayrıştırma mantığı karmaşık ve kırılgan. Daha güvenilir bir
            # veri yapısı (örn. JSON) tavsiye edilir.
            parts = item.split('-')
            if len(parts) >= 2:
                malzeme_adi = parts[0].strip().lower()
                miktar_birim = parts[1].strip()

                try:
                    miktar_parts = miktar_birim.split()
                    miktar = float(miktar_parts[0]) if miktar_parts and miktar_parts[0].replace('.', '', 1).isdigit() else 1
                    birim = miktar_parts[1] if len(miktar_parts) > 1 else "adet"
                except Exception:
                    miktar = 1
                    birim = "adet"

                # Miktar karşılaştırması olmadan sadece evde var mı yok mu kontrolü
                if malzeme_adi not in user_malzeme_dict:
                    eksik_malzemeler.append({
                        "name": malzeme_adi,
                        "miktar": miktar,
                        "birim": birim
                    })
                    logger.debug(f"Eksik malzeme bulundu: {malzeme_adi}")
                else:
                    logger.debug(f"Evde mevcut: {malzeme_adi}")


        logger.info(f"Toplam {len(eksik_malzemeler)} eksik malzeme tespit edildi.")

        alisveris_listesi = AlisverisListesi(
            user_id=user_id,
            durum="aktif",
            notlar=f"{len(eksik_malzemeler)} eksik malzeme"
        )
        db.add(alisveris_listesi)
        db.flush() # ID almak için commit öncesi flush

        logger.info(f"Yeni alışveriş listesi oluşturuldu, ID: {alisveris_listesi.id}")

        for item in eksik_malzemeler:
            malzeme = db.query(Malzeme).filter(Malzeme.name == item["name"]).first()

            if not malzeme:
                malzeme = Malzeme(name=item["name"], category="genel")
                db.add(malzeme)
                db.flush() # ID almak için commit öncesi flush

            alisveris_urunu = AlisverisUrunu(
                liste_id=alisveris_listesi.id,
                malzeme_id=malzeme.id,
                miktar=item["miktar"],
                birim=item["birim"],
                alinma_durumu=False
            )
            db.add(alisveris_urunu)

        db.commit()
        logger.info("Alışveriş listesi ve ürünleri başarıyla veritabanına kaydedildi.")

        return {
            "success": True,
            "eksik_malzemeler": eksik_malzemeler,
            "liste_id": alisveris_listesi.id,
            "message": f"{len(eksik_malzemeler)} eksik malzeme bulundu"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Alışveriş listesi oluşturulurken kritik hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Alışveriş listesi oluşturulurken bir sunucu hatası oluştu.")


@router.get("/listeler")
async def alisveris_listeler( current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """Kullanıcının tüm alışveriş listelerini getir"""
    user_id = current_user.id  # Kimlik doğrulama sonrası güncellenecek
    logger.info(f"Kullanıcı {user_id} için alışveriş listesi oluşturuluyor.")

    listeler = db.query(AlisverisListesi).filter(
        AlisverisListesi.user_id == user_id
    ).order_by(AlisverisListesi.olusturma_tarihi.desc()).all()

    result = []
    for liste in listeler:
        urunler = db.query(AlisverisUrunu).filter(
            AlisverisUrunu.liste_id == liste.id
        ).all()

        urun_listesi = []
        tamamlanan_sayisi = 0

        for urun in urunler:
            malzeme = db.query(Malzeme).filter(Malzeme.id == urun.malzeme_id).first()
            if malzeme:
                urun_listesi.append({
                    "id": urun.id,
                    "name": malzeme.name,
                    "miktar": urun.miktar,
                    "birim": urun.birim,
                    "alinma_durumu": urun.alinma_durumu
                })
                if urun.alinma_durumu:
                    tamamlanan_sayisi += 1

        result.append({
            "id": liste.id,
            "olusturma_tarihi": liste.olusturma_tarihi.isoformat(),
            "durum": liste.durum,
            "notlar": liste.notlar,
            "toplam_urun": len(urun_listesi),
            "tamamlanan_urun": tamamlanan_sayisi,
            "urunler": urun_listesi
        })

    return {
        "success": True,
        "listeler": result
    }


@router.get("/{liste_id}")
async def alisveris_detay(liste_id: int , current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Alışveriş listesi detayı"""
    user_id = current_user.id # Kimlik doğrulama sonrası güncellenecek
    logger.info(f"Kullanıcı {user_id} için alışveriş listesi detayı oluşturuluyor.")

    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == user_id
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    urunler = db.query(AlisverisUrunu).filter(
        AlisverisUrunu.liste_id == liste.id
    ).all()

    urun_listesi = []
    for urun in urunler:
        malzeme = db.query(Malzeme).filter(Malzeme.id == urun.malzeme_id).first()
        if malzeme:
            urun_listesi.append({
                "id": urun.id,
                "name": malzeme.name,
                "miktar": urun.miktar,
                "birim": urun.birim,
                "alinma_durumu": urun.alinma_durumu
            })

    return {
        "success": True,
        "liste": {
            "id": liste.id,
            "olusturma_tarihi": liste.olusturma_tarihi.isoformat(),
            "durum": liste.durum,
            "notlar": liste.notlar,
            "urunler": urun_listesi
        }
    }


@router.post("/{liste_id}/urun")
async def alisveris_urun_ekle(
    liste_id: int,
    malzeme_adi: str = Body(...),
    miktar: float = Body(...),
    birim: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alışveriş listesine yeni ürün ekle"""
    user_id = current_user.id # Kimlik doğrulama sonrası güncellenecek
    logger.info(f"Kullanıcı {user_id} için alışveriş urun ekleniyor.")

    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == user_id
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    malzeme = db.query(Malzeme).filter(Malzeme.name == malzeme_adi.lower()).first()

    if not malzeme:
        malzeme = Malzeme(name=malzeme_adi.lower(), category="genel")
        db.add(malzeme)
        db.commit()
        db.refresh(malzeme)

    urun = AlisverisUrunu(
        liste_id=liste_id,
        malzeme_id=malzeme.id,
        miktar=miktar,
        birim=birim,
        alinma_durumu=False
    )
    db.add(urun)
    db.commit()

    toplam_urun = db.query(AlisverisUrunu).filter(
        AlisverisUrunu.liste_id == liste_id
    ).count()

    liste.notlar = f"{toplam_urun} ürün"
    db.commit()

    return {
        "success": True,
        "message": "Ürün eklendi"
    }


@router.put("/urun/{urun_id}/durum")
async def alisveris_urun_durum(
    urun_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alışveriş ürünü durumunu güncelle"""
    user_id = current_user.id # Kimlik doğrulama sonrası güncellenecek
    logger.info(f"Kullanıcı {user_id} için alışveriş durumu alınıyor")

    alinma_durumu = request.get("alinma_durumu")

    logger.info(f"Ürün durumu güncelleme isteği. Ürün ID: {urun_id}, Yeni durum: {alinma_durumu}")

    urun = db.query(AlisverisUrunu).filter(AlisverisUrunu.id == urun_id).first()

    if not urun:
        logger.warning(f"Ürün ID {urun_id} bulunamadı.")
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    try:
        urun.alinma_durumu = alinma_durumu
        db.commit()
        logger.info(f"Ürün ID {urun_id} durumu başarıyla kaydedildi: {alinma_durumu}")
    except Exception as e:
        db.rollback()
        logger.error(f"Ürün durumu güncellenirken hata: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Durum güncellenirken sunucu hatası.")

    return {
        "success": True,
        "message": "Durum güncellendi"
    }


@router.delete("/urun/{urun_id}")
async def alisveris_urun_sil(urun_id: int , current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Alışveriş listesinden ürün sil"""
    user_id = current_user.id # Kimlik doğrulama sonrası güncellenecek
    logger.info(f"Kullanıcı {user_id} için alışveriş urun silme.")

    urun = db.query(AlisverisUrunu).filter(AlisverisUrunu.id == urun_id).first()

    if not urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    liste_id = urun.liste_id

    db.delete(urun)
    db.commit()

    toplam_urun = db.query(AlisverisUrunu).filter(
        AlisverisUrunu.liste_id == liste_id
    ).count()

    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id
    ).first()

    if liste:
        liste.notlar = f"{toplam_urun} ürün" if toplam_urun > 0 else "Liste boş"
        db.commit()

    return {
        "success": True,
        "message": "Ürün silindi"
    }


@router.put("/{liste_id}/tamamla")
async def alisveris_tamamla(liste_id: int , current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Alışveriş listesini tamamla"""
    user_id = current_user.id
    logger.info(f"Kullanıcı {user_id} için alışveriş tamamlama.")

    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == user_id
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    liste.durum = "tamamlandi"
    db.commit()

    return {
        "success": True,
        "message": "Liste tamamlandı"
    }


@router.delete("/{liste_id}")
async def alisveris_sil(liste_id: int , current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Alışveriş listesini sil"""
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == current_user.id
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    db.query(AlisverisUrunu).filter(AlisverisUrunu.liste_id == liste_id).delete()
    db.delete(liste)
    db.commit()

    return {
        "success": True,
        "message": "Liste silindi"
    }
