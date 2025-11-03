"""
Alışveriş Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AlisverisListesi, AlisverisUrunu, Malzeme, KullaniciMalzeme
from app.schemas.alisveris import AlisverisOlustur, AlisverisUrunDurum

router = APIRouter(prefix="/api/alisveris", tags=["Alışveriş"])


@router.post("/olustur")
async def alisveris_olustur(request: AlisverisOlustur, db: Session = Depends(get_db)):
    """Tarifteki malzemelerden alışveriş listesi oluştur"""
    print("=" * 50)
    print("🛒 Alışveriş listesi oluşturuluyor...")
    print(f"📦 Gelen malzemeler: {request.malzemeler}")
    
    try:
        tarif_malzemeleri = request.malzemeler
        print(f"📋 Tarif malzemeleri sayısı: {len(tarif_malzemeleri)}")

        if not tarif_malzemeleri:
            print("❌ Malzeme listesi boş!")
            raise HTTPException(status_code=400, detail="Malzeme listesi boş")

        user_malzemeler = db.query(KullaniciMalzeme).filter(
            KullaniciMalzeme.user_id == 1
        ).all()

        user_malzeme_dict = {}
        for um in user_malzemeler:
            malzeme = db.query(Malzeme).filter(Malzeme.id == um.malzeme_id).first()
            if malzeme:
                user_malzeme_dict[malzeme.name.lower()] = um.miktar

        print(f"🏠 Evdeki malzemeler: {list(user_malzeme_dict.keys())}")

        eksik_malzemeler = []

        for item in tarif_malzemeleri:
            print(f"   İşleniyor: {item}")
            parts = item.split('-')
            if len(parts) >= 2:
                malzeme_adi = parts[0].strip().lower()
                miktar_birim = parts[1].strip()

                miktar_parts = miktar_birim.split()
                try:
                    miktar = float(miktar_parts[0]) if miktar_parts else 1
                    birim = miktar_parts[1] if len(miktar_parts) > 1 else "adet"
                except:
                    miktar = 1
                    birim = "adet"

                if malzeme_adi not in user_malzeme_dict:
                    eksik_malzemeler.append({
                        "name": malzeme_adi,
                        "miktar": miktar,
                        "birim": birim
                    })
                    print(f"      ❌ Eksik: {malzeme_adi}")
                else:
                    print(f"      ✅ Var: {malzeme_adi}")

        print(f"📝 Toplam eksik malzeme: {len(eksik_malzemeler)}")

        alisveris_listesi = AlisverisListesi(
            user_id=1,
            durum="aktif",
            notlar=f"{len(eksik_malzemeler)} eksik malzeme"
        )
        db.add(alisveris_listesi)
        db.commit()
        db.refresh(alisveris_listesi)

        print(f"✅ Liste oluşturuldu, ID: {alisveris_listesi.id}")

        for item in eksik_malzemeler:
            malzeme = db.query(Malzeme).filter(Malzeme.name == item["name"]).first()

            if not malzeme:
                malzeme = Malzeme(name=item["name"], category="genel")
                db.add(malzeme)
                db.commit()
                db.refresh(malzeme)

            alisveris_urunu = AlisverisUrunu(
                liste_id=alisveris_listesi.id,
                malzeme_id=malzeme.id,
                miktar=item["miktar"],
                birim=item["birim"],
                alinma_durumu=False
            )
            db.add(alisveris_urunu)

        db.commit()

        print("✅ Alışveriş listesi başarıyla kaydedildi!")
        print("=" * 50)

        return {
            "success": True,
            "eksik_malzemeler": eksik_malzemeler,
            "liste_id": alisveris_listesi.id,
            "message": f"{len(eksik_malzemeler)} eksik malzeme bulundu"
        }

    except Exception as e:
        print(f"❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listeler")
async def alisveris_listeler(db: Session = Depends(get_db)):
    """Kullanıcının tüm alışveriş listelerini getir"""
    listeler = db.query(AlisverisListesi).filter(
        AlisverisListesi.user_id == 1
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
async def alisveris_detay(liste_id: int, db: Session = Depends(get_db)):
    """Alışveriş listesi detayı"""
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == 1
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
    db: Session = Depends(get_db)
):
    """Alışveriş listesine yeni ürün ekle"""
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == 1
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
    db: Session = Depends(get_db)
):
    """Alışveriş ürünü durumunu güncelle"""
    alinma_durumu = request.get("alinma_durumu")
    
    print("=" * 50)
    print(f"📦 Ürün durumu güncelleme isteği")
    print(f"   Ürün ID: {urun_id}")
    print(f"   Yeni durum: {alinma_durumu}")
    
    urun = db.query(AlisverisUrunu).filter(AlisverisUrunu.id == urun_id).first()
    
    if not urun:
        print(f"❌ Ürün {urun_id} bulunamadı")
        print("=" * 50)
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    print(f"   Eski durum: {urun.alinma_durumu}")
    urun.alinma_durumu = alinma_durumu
    db.commit()
    print(f"   ✅ Yeni durum kaydedildi: {urun.alinma_durumu}")
    print("=" * 50)
    
    return {
        "success": True,
        "message": "Durum güncellendi"
    }


@router.delete("/urun/{urun_id}")
async def alisveris_urun_sil(urun_id: int, db: Session = Depends(get_db)):
    """Alışveriş listesinden ürün sil"""
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
async def alisveris_tamamla(liste_id: int, db: Session = Depends(get_db)):
    """Alışveriş listesini tamamla"""
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == 1
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
async def alisveris_sil(liste_id: int, db: Session = Depends(get_db)):
    """Alışveriş listesini sil"""
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == 1
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
