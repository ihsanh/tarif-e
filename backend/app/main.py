"""
Tarif-e FastAPI Ana Uygulama
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import shutil
import os
from pathlib import Path

from .config import settings
from .database import engine, Base, get_db, init_db
from .services.ai_service import ai_service

print("🔥 MAIN.PY YÜKLENDI! 🔥")

# Veritabanını başlat
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Akıllı Mutfak Asistanı - Malzemeden Tarife, Tariften Alışverişe",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# Pydantic models
class MalzemeEkle(BaseModel):
    name: str
    miktar: Optional[float] = 1.0
    birim: Optional[str] = "adet"

class TarifOner(BaseModel):
    malzemeler: List[str]
    sure: Optional[int] = None
    zorluk: Optional[str] = None
    kategori: Optional[str] = None

class AlisverisRequest(BaseModel):
    malzemeler: List[str]


# Routes

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa():
    """Ana sayfa"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return """
    <html>
        <head><title>Tarif-e</title></head>
        <body>
            <h1>🍳 Tarif-e - Akıllı Mutfak Asistanı</h1>
            <p>API çalışıyor! Frontend dosyaları yükleniyor...</p>
            <p>API Dokümantasyonu: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "ai_enabled": ai_service.enabled,
        "ai_mode": settings.AI_MODE
    }


@app.post("/api/malzeme/tani")
async def malzeme_tani(file: UploadFile = File(...)):
    """
    Fotoğraftan malzeme tanıma

    - AI kullanarak fotoğraftaki malzemeleri tespit eder
    - Kullanıcı ayarlarına göre AI kullanımı kontrol edilir
    """
    if not ai_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI servisi aktif değil. GEMINI_API_KEY ayarlanmalı."
        )

    try:
        # Dosyayı kaydet
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # AI ile malzemeleri tanı
        malzemeler = ai_service.malzeme_tani(str(file_path))

        # Dosyayı sil (opsiyonel - veya sakla)
        # file_path.unlink()

        return {
            "success": True,
            "malzemeler": malzemeler,
            "count": len(malzemeler)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/malzeme/ekle")
async def malzeme_ekle(malzeme: MalzemeEkle, db: Session = Depends(get_db)):
    """
    Manuel malzeme ekleme - Varsa miktarı artır
    """
    from .database import Malzeme, KullaniciMalzeme

    # Malzeme var mı kontrol et
    db_malzeme = db.query(Malzeme).filter(Malzeme.name == malzeme.name.lower()).first()

    # Yoksa oluştur
    if not db_malzeme:
        db_malzeme = Malzeme(
            name=malzeme.name.lower(),
            category="genel"
        )
        db.add(db_malzeme)
        db.commit()
        db.refresh(db_malzeme)

    # Kullanıcının bu malzemesi var mı kontrol et
    kullanici_malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.user_id == 1,
        KullaniciMalzeme.malzeme_id == db_malzeme.id
    ).first()

    if kullanici_malzeme:
        # Varsa miktarı artır
        kullanici_malzeme.miktar += malzeme.miktar
        message = f"{malzeme.name} miktarı güncellendi ({kullanici_malzeme.miktar} {kullanici_malzeme.birim})"
    else:
        # Yoksa yeni ekle
        kullanici_malzeme = KullaniciMalzeme(
            user_id=1,
            malzeme_id=db_malzeme.id,
            miktar=malzeme.miktar,
            birim=malzeme.birim
        )
        db.add(kullanici_malzeme)
        message = f"{malzeme.name} eklendi"

    db.commit()
    db.refresh(kullanici_malzeme)

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


@app.get("/api/malzeme/liste")
async def malzeme_liste(db: Session = Depends(get_db)):
    """
    Kullanıcının malzeme listesi
    """
    from .database import KullaniciMalzeme, Malzeme

    # Kullanıcının malzemelerini çek (şimdilik user_id=1)
    user_malzemeler = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.user_id == 1
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

    return {
        "malzemeler": malzemeler
    }


@app.delete("/api/malzeme/{malzeme_id}")
async def malzeme_sil(malzeme_id: int, db: Session = Depends(get_db)):
    """
    Malzeme sil
    """
    from .database import KullaniciMalzeme

    malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.id == malzeme_id,
        KullaniciMalzeme.user_id == 1  # TODO: Gerçek user
    ).first()

    if not malzeme:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")

    db.delete(malzeme)
    db.commit()

    return {"success": True, "message": "Malzeme silindi"}


@app.post("/api/tarif/oner")
async def tarif_oner(request: TarifOner):
    """
    Malzemelerden tarif öner

    - AI kullanarak tarif üretir
    - Kullanıcı tercihlerini dikkate alır
    """
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


@app.post("/api/alisveris/olustur")
async def alisveris_olustur(request: dict, db: Session = Depends(get_db)):
    print("🔥 alışveris YÜKLENDI! 🔥")

    """
    Tarifteki malzemelerden alışveriş listesi oluştur
    """
    from .database import AlisverisListesi, AlisverisUrunu, Malzeme, KullaniciMalzeme

    print("=" * 50)
    print("🛒 Alışveriş listesi oluşturuluyor...")
    print(f"📦 Gelen request: {request}")

    try:
        # dict'ten malzemeleri çıkar
        tarif_malzemeleri = request.get("malzemeler", [])
        print(f"📋 Malzemeler: {tarif_malzemeleri}")

        if not tarif_malzemeleri:
            return {"success": False, "message": "Malzeme listesi boş"}

        # Kullanıcının mevcut malzemelerini al
        user_malzemeler = db.query(KullaniciMalzeme).filter(
            KullaniciMalzeme.user_id == 1
        ).all()

        user_malzeme_dict = {}
        for um in user_malzemeler:
            malzeme = db.query(Malzeme).filter(Malzeme.id == um.malzeme_id).first()
            if malzeme:
                user_malzeme_dict[malzeme.name.lower()] = um.miktar

        print(f"🏠 Evdeki malzemeler: {list(user_malzeme_dict.keys())}")

        # Eksik malzemeleri bul
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

        print(f"📝 Toplam eksik: {len(eksik_malzemeler)}")

        # Liste oluştur
        alisveris_listesi = AlisverisListesi(
            user_id=1,
            durum="aktif",
            notlar=f"{len(eksik_malzemeler)} eksik malzeme"
        )
        db.add(alisveris_listesi)
        db.commit()
        db.refresh(alisveris_listesi)

        print(f"✅ Liste ID: {alisveris_listesi.id}")

        # Ürünleri ekle
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
        print("✅ Başarılı!")
        print("=" * 50)

        return {
            "success": True,
            "eksik_malzemeler": eksik_malzemeler,
            "liste_id": alisveris_listesi.id,
            "message": f"{len(eksik_malzemeler)} eksik malzeme"
        }

    except Exception as e:
        print(f"❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return {"success": False, "message": str(e)}

@app.get("/api/ayarlar")
async def ayarlar_getir():
    """Kullanıcı ayarlarını getir"""
    return {
        "ai_mode": settings.AI_MODE,
        "ai_quota": settings.MAX_FREE_AI_REQUESTS,
        "data_sharing": True
    }


@app.put("/api/malzeme/{malzeme_id}")
async def malzeme_guncelle(
        malzeme_id: int,
        miktar: float = Body(...),
        birim: str = Body(...),
        db: Session = Depends(get_db)
):
    """
    Malzeme miktarını güncelle
    """
    from .database import KullaniciMalzeme

    malzeme = db.query(KullaniciMalzeme).filter(
        KullaniciMalzeme.id == malzeme_id,
        KullaniciMalzeme.user_id == 1
    ).first()

    if not malzeme:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")

    malzeme.miktar = miktar
    malzeme.birim = birim
    db.commit()

    return {
        "success": True,
        "message": "Malzeme güncellendi",
        "malzeme": {
            "id": malzeme.id,
            "miktar": malzeme.miktar,
            "birim": malzeme.birim
        }
    }


@app.get("/api/alisveris/listeler")
async def alisveris_listeler(db: Session = Depends(get_db)):
    """
    Kullanıcının tüm alışveriş listelerini getir
    """
    from .database import AlisverisListesi, AlisverisUrunu, Malzeme

    # Kullanıcının listelerini çek (en yeni önce)
    listeler = db.query(AlisverisListesi).filter(
        AlisverisListesi.user_id == 1
    ).order_by(AlisverisListesi.olusturma_tarihi.desc()).all()

    result = []
    for liste in listeler:
        # Liste ürünlerini çek
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


@app.get("/api/alisveris/{liste_id}")
async def alisveris_detay(liste_id: int, db: Session = Depends(get_db)):
    """
    Alışveriş listesi detayı
    """
    from .database import AlisverisListesi, AlisverisUrunu, Malzeme

    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == 1
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    # Liste ürünlerini çek
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


@app.put("/api/alisveris/urun/{urun_id}/durum")
async def alisveris_urun_durum(urun_id: int, request: dict, db: Session = Depends(get_db)):
    """
    Alışveriş ürünü durumunu güncelle (alındı/alınmadı)
    """
    from .database import AlisverisUrunu

    alinma_durumu = request.get("alinma_durumu")

    print("=" * 50)
    print(f"📦 Ürün durumu güncelleme isteği")
    print(f"   Ürün ID: {urun_id}")
    print(f"   Yeni durum: {alinma_durumu}")
    print(f"   Request: {request}")

    urun = db.query(AlisverisUrunu).filter(
        AlisverisUrunu.id == urun_id
    ).first()

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


@app.put("/api/alisveris/{liste_id}/tamamla")
async def alisveris_tamamla(liste_id: int, db: Session = Depends(get_db)):
    """
    Alışveriş listesini tamamla
    """
    from .database import AlisverisListesi

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


@app.delete("/api/alisveris/{liste_id}")
async def alisveris_sil(liste_id: int, db: Session = Depends(get_db)):
    """
    Alışveriş listesini sil
    """
    from .database import AlisverisListesi, AlisverisUrunu

    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == 1
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    # Önce ürünleri sil
    db.query(AlisverisUrunu).filter(AlisverisUrunu.liste_id == liste_id).delete()

    # Sonra listeyi sil
    db.delete(liste)
    db.commit()

    return {
        "success": True,
        "message": "Liste silindi"
    }


@app.post("/api/alisveris/{liste_id}/urun")
async def alisveris_urun_ekle(
        liste_id: int,
        malzeme_adi: str = Body(...),
        miktar: float = Body(...),
        birim: str = Body(...),
        db: Session = Depends(get_db)
):
    """
    Alışveriş listesine yeni ürün ekle
    """
    from .database import AlisverisListesi, AlisverisUrunu, Malzeme

    # Liste var mı kontrol et
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == 1
    ).first()

    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")

    # Malzeme var mı kontrol et
    malzeme = db.query(Malzeme).filter(Malzeme.name == malzeme_adi.lower()).first()

    if not malzeme:
        malzeme = Malzeme(name=malzeme_adi.lower(), category="genel")
        db.add(malzeme)
        db.commit()
        db.refresh(malzeme)

    # Ürünü ekle
    urun = AlisverisUrunu(
        liste_id=liste_id,
        malzeme_id=malzeme.id,
        miktar=miktar,
        birim=birim,
        alinma_durumu=False
    )
    db.add(urun)
    db.commit()

    # Liste notlarını güncelle
    toplam_urun = db.query(AlisverisUrunu).filter(
        AlisverisUrunu.liste_id == liste_id
    ).count()

    liste.notlar = f"{toplam_urun} ürün"
    db.commit()

    return {
        "success": True,
        "message": "Ürün eklendi"
    }


@app.delete("/api/alisveris/urun/{urun_id}")
async def alisveris_urun_sil(urun_id: int, db: Session = Depends(get_db)):
    """
    Alışveriş listesinden ürün sil
    """
    from .database import AlisverisUrunu, AlisverisListesi

    urun = db.query(AlisverisUrunu).filter(AlisverisUrunu.id == urun_id).first()

    if not urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    liste_id = urun.liste_id

    db.delete(urun)
    db.commit()

    # Liste notlarını güncelle
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


import json


class TarifFavori(BaseModel):
    tarif: dict


import json
from typing import List, Optional
from pydantic import BaseModel


# Pydantic model
class TarifFavori(BaseModel):
    tarif: dict


# Favorilere ekle
# ÖNCE spesifik route'lar

# Favorilere ekle
@app.post("/api/tarif/favori")
async def tarif_favori_ekle(request: TarifFavori, db: Session = Depends(get_db)):
    """
    Tarifi favorilere ekle
    """
    from .database import FavoriTarif

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


# Favorileri listele - ÖNEMLİ: Bu /api/tarif/{tarif_id}'den ÖNCE olmali
@app.get("/api/tarif/favoriler")
async def tarif_favoriler(db: Session = Depends(get_db)):
    """
    Favori tarifleri listele
    """
    from .database import FavoriTarif

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


# Favoriden sil
@app.delete("/api/tarif/favori/{favori_id}")
async def tarif_favori_sil(favori_id: int, db: Session = Depends(get_db)):
    """
    Favori tarifi sil
    """
    from .database import FavoriTarif

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

class AyarlarGuncelle(BaseModel):
    ai_mode: str


@app.post("/api/ayarlar")
async def ayarlar_guncelle(ayarlar: AyarlarGuncelle):
    """Kullanıcı ayarlarını güncelle"""
    if ayarlar.ai_mode not in ["auto", "manual", "hybrid", "off"]:
        raise HTTPException(status_code=400, detail="Geçersiz AI modu")

    # TODO: Veritabanına kaydet
    return {
        "success": True,
        "ai_mode": ayarlar.ai_mode
    }


# Uygulama başlatma eventi
@app.on_event("startup")
async def startup_event():
    """Uygulama başlarken"""
    print("=" * 50)
    print(f"🍳 {settings.APP_NAME} başlatılıyor...")
    print(f"📊 Debug modu: {settings.DEBUG}")
    print(f"🤖 AI aktif: {ai_service.enabled}")
    print(f"⚙️  AI modu: {settings.AI_MODE}")
    print(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )