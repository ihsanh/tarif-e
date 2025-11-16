"""
Alışveriş Listesi Geliştirmeleri - API Routes
backend/app/routes/alisveris_extended.py (YENİ DOSYA)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, AlisverisListesi, AlisverisUrunu, ListePaylasim, MalzemeKategorisi , PaylaşımRolü
from app.schemas import (
    ListePaylasimCreate, ListePaylasimUpdate, ListePaylasimResponse,
    PaylasilanListeResponse, GrupluListeResponse, KategoriGrubu,
    kategori_turkce_adi
)
from app.utils.auth import get_current_user
from collections import defaultdict

router = APIRouter(prefix="/api/alisveris", tags=["Alışveriş - Gelişmiş"])


# ============================================
# 1. LİSTE PAYLAŞMA
# ============================================

@router.post("/paylas", response_model=dict)
async def liste_paylas(
    paylasim: ListePaylasimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Alışveriş listesini başka kullanıcıyla paylaş
    
    - Liste sahibi olmalısınız
    - Email veya username ile paylaşabilirsiniz
    - Görüntüleme veya düzenleme yetkisi verebilirsiniz
    """
    # Liste var mı ve sahibi mi kontrol et
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == paylasim.liste_id,
        AlisverisListesi.user_id == current_user.id
    ).first()
    
    if not liste:
        raise HTTPException(
            status_code=404,
            detail="Liste bulunamadı veya paylaşma yetkiniz yok"
        )
    
    # Paylaşılacak kullanıcıyı bul (email veya username)
    paylasilan_user = db.query(User).filter(
        (User.email == paylasim.paylasilan_email_veya_username) |
        (User.username == paylasim.paylasilan_email_veya_username)
    ).first()
    
    if not paylasilan_user:
        raise HTTPException(
            status_code=404,
            detail="Kullanıcı bulunamadı"
        )
    
    # Kendinle paylaşamazsın
    if paylasilan_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Listeyi kendinizle paylaşamazsınız"
        )
    
    # Zaten paylaşılmış mı kontrol et
    mevcut_paylasim = db.query(ListePaylasim).filter(
        ListePaylasim.liste_id == paylasim.liste_id,
        ListePaylasim.paylasilan_user_id == paylasilan_user.id
    ).first()
    
    if mevcut_paylasim:
        raise HTTPException(
            status_code=400,
            detail=f"Liste zaten {paylasilan_user.username} ile paylaşılmış"
        )
    
    # Paylaşımı oluştur
    yeni_paylasim = ListePaylasim(
        liste_id=paylasim.liste_id,
        paylasan_user_id=current_user.id,
        paylasilan_user_id=paylasilan_user.id,
        rol=paylasim.rol,
        kabul_edildi=False  # Kullanıcı kabul etmeli
    )
    
    db.add(yeni_paylasim)
    db.commit()
    db.refresh(yeni_paylasim)
    
    return {
        "success": True,
        "message": f"Liste {paylasilan_user.username} ile paylaşıldı",
        "paylasim_id": yeni_paylasim.id,
        "bekleyen_onay": not yeni_paylasim.kabul_edildi
    }


@router.get("/benimle-paylasilan", response_model=List[PaylasilanListeResponse])
async def benimle_paylasilan_listeler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Benimle paylaşılan alışveriş listelerini getir
    """
    paylasilmalar = db.query(ListePaylasim).filter(
        ListePaylasim.paylasilan_user_id == current_user.id
    ).all()
    
    sonuc = []
    for paylasim in paylasilmalar:
        liste = db.query(AlisverisListesi).filter(
            AlisverisListesi.id == paylasim.liste_id
        ).first()
        
        if liste:
            paylasan = db.query(User).filter(
                User.id == paylasim.paylasan_user_id
            ).first()
            
            urun_sayisi = db.query(AlisverisUrunu).filter(
                AlisverisUrunu.liste_id == liste.id
            ).count()
            
            sonuc.append({
                "liste_id": liste.id,
                "liste_baslik": liste.baslik,
                "paylasan_username": paylasan.username if paylasan else "Bilinmeyen",
                "rol": paylasim.rol,
                "paylasim_tarihi": paylasim.paylasim_tarihi,
                "kabul_edildi": paylasim.kabul_edildi,
                "urun_sayisi": urun_sayisi
            })
    
    return sonuc


@router.post("/paylasim/{paylasim_id}/kabul", response_model=dict)
async def paylasimi_kabul_et(
    paylasim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Benimle paylaşılan listeyi kabul et
    """
    paylasim = db.query(ListePaylasim).filter(
        ListePaylasim.id == paylasim_id,
        ListePaylasim.paylasilan_user_id == current_user.id
    ).first()
    
    if not paylasim:
        raise HTTPException(
            status_code=404,
            detail="Paylaşım bulunamadı"
        )
    
    paylasim.kabul_edildi = True
    db.commit()
    
    return {
        "success": True,
        "message": "Paylaşım kabul edildi"
    }


@router.delete("/paylasim/{paylasim_id}", response_model=dict)
async def paylasimi_kaldir(
    paylasim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Paylaşımı kaldır (paylaşan veya paylaşılan yapabilir)
    """
    paylasim = db.query(ListePaylasim).filter(
        ListePaylasim.id == paylasim_id,
        (ListePaylasim.paylasan_user_id == current_user.id) |
        (ListePaylasim.paylasilan_user_id == current_user.id)
    ).first()
    
    if not paylasim:
        raise HTTPException(
            status_code=404,
            detail="Paylaşım bulunamadı"
        )
    
    db.delete(paylasim)
    db.commit()
    
    return {
        "success": True,
        "message": "Paylaşım kaldırıldı"
    }


@router.get("/{liste_id}/paylasimlar", response_model=List[ListePaylasimResponse])
async def liste_paylasimlarini_getir(
    liste_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bir listenin tüm paylaşımlarını getir (sadece liste sahibi)
    """
    # Liste sahibi mi kontrol et
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id,
        AlisverisListesi.user_id == current_user.id
    ).first()
    
    if not liste:
        raise HTTPException(
            status_code=404,
            detail="Liste bulunamadı veya yetkiniz yok"
        )
    
    paylasilmalar = db.query(ListePaylasim).filter(
        ListePaylasim.liste_id == liste_id
    ).all()
    
    sonuc = []
    for paylasim in paylasilmalar:
        paylasan = db.query(User).filter(User.id == paylasim.paylasan_user_id).first()
        paylasilan = db.query(User).filter(User.id == paylasim.paylasilan_user_id).first()
        
        sonuc.append({
            "id": paylasim.id,
            "liste_id": paylasim.liste_id,
            "paylasan_user_id": paylasim.paylasan_user_id,
            "paylasilan_user_id": paylasim.paylasilan_user_id,
            "paylasan_username": paylasan.username if paylasan else "Bilinmeyen",
            "paylasilan_username": paylasilan.username if paylasilan else "Bilinmeyen",
            "rol": paylasim.rol,
            "paylasim_tarihi": paylasim.paylasim_tarihi,
            "kabul_edildi": paylasim.kabul_edildi
        })
    
    return sonuc


# ============================================
# 2. KATEGORİ GRUPLAMA
# ============================================

@router.get("/{liste_id}/kategoriler", response_model=GrupluListeResponse)
async def liste_kategoriye_gore_grupla(
    liste_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Alışveriş listesini kategoriye göre grupla
    
    - Ürünler kategorilerine göre gruplanır
    - Her kategori için ürün sayısı gösterilir
    """
    # Liste var mı ve erişim yetkisi var mı kontrol et
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id
    ).first()
    
    if not liste:
        raise HTTPException(
            status_code=404,
            detail="Liste bulunamadı"
        )
    
    # Erişim kontrolü (sahip mi veya paylaşılmış mı)
    if liste.user_id != current_user.id:
        paylasim = db.query(ListePaylasim).filter(
            ListePaylasim.liste_id == liste_id,
            ListePaylasim.paylasilan_user_id == current_user.id,
            ListePaylasim.kabul_edildi == True
        ).first()
        
        if not paylasim:
            raise HTTPException(
                status_code=403,
                detail="Bu listeye erişim yetkiniz yok"
            )
    
    # Ürünleri getir
    urunler = db.query(AlisverisUrunu).filter(
        AlisverisUrunu.liste_id == liste_id
    ).all()
    
    # Kategoriye göre grupla
    kategori_dict = defaultdict(list)
    for urun in urunler:
        kategori_dict[urun.kategori].append({
            "id": urun.id,
            "liste_id": urun.liste_id,
            "malzeme_adi": urun.malzeme_adi,
            "miktar": urun.miktar,
            "birim": urun.birim,
            "kategori": urun.kategori,
            "alinan": urun.alinan
        })
    
    # Response oluştur
    kategoriler = []
    for kategori, urun_listesi in kategori_dict.items():
        kategoriler.append({
            "kategori": kategori,
            "kategori_adi": kategori_turkce_adi(kategori),
            "urunler": urun_listesi,
            "toplam_urun": len(urun_listesi)
        })
    
    # Kategorileri sırala (alfabetik)
    kategoriler.sort(key=lambda x: x["kategori_adi"])
    
    return {
        "liste_id": liste.id,
        "liste_baslik": liste.baslik,
        "kategoriler": kategoriler,
        "toplam_kategori": len(kategoriler),
        "toplam_urun": len(urunler)
    }


@router.post("/{liste_id}/urun/{urun_id}/kategori", response_model=dict)
async def urun_kategorisini_guncelle(
    liste_id: int,
    urun_id: int,
    yeni_kategori: MalzemeKategorisi,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ürünün kategorisini güncelle
    """
    # Liste erişim kontrolü
    liste = db.query(AlisverisListesi).filter(
        AlisverisListesi.id == liste_id
    ).first()
    
    if not liste:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")
    
    # Düzenleme yetkisi var mı kontrol et
    if liste.user_id != current_user.id:
        paylasim = db.query(ListePaylasim).filter(
            ListePaylasim.liste_id == liste_id,
            ListePaylasim.paylasilan_user_id == current_user.id,
            ListePaylasim.kabul_edildi == True,
            ListePaylasim.rol == PaylaşımRolü.DUZENLEYEBILIR
        ).first()
        
        if not paylasim:
            raise HTTPException(
                status_code=403,
                detail="Düzenleme yetkiniz yok"
            )
    
    # Ürünü güncelle
    urun = db.query(AlisverisUrunu).filter(
        AlisverisUrunu.id == urun_id,
        AlisverisUrunu.liste_id == liste_id
    ).first()
    
    if not urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    eski_kategori = urun.kategori
    urun.kategori = yeni_kategori
    db.commit()
    
    return {
        "success": True,
        "message": f"Kategori güncellendi: {kategori_turkce_adi(eski_kategori)} → {kategori_turkce_adi(yeni_kategori)}",
        "eski_kategori": eski_kategori,
        "yeni_kategori": yeni_kategori
    }


# ============================================
# KATEGORİ TAHMİN FONKSİYONU
# ============================================

def kategori_tahmin_et(malzeme_adi: str) -> MalzemeKategorisi:
    """
    Malzeme adından kategoriyi tahmin et (basit keyword matching)
    """
    malzeme_adi_lower = malzeme_adi.lower()
    
    # Meyve & Sebze
    if any(kelime in malzeme_adi_lower for kelime in ["domates", "salatalık", "biber", "soğan", "elma", "muz", "portakal", "üzüm", "çilek", "kiraz", "kavun", "karpuz", "havuç", "patates", "kabak", "patlıcan", "marul", "maydanoz", "taze soğan", "mantar"]):
        return MalzemeKategorisi.MEYVE_SEBZE
    
    # Et, Tavuk & Balık
    if any(kelime in malzeme_adi_lower for kelime in ["et", "tavuk", "balık", "köfte", "dana", "kuzu", "hindi", "sosis", "sucuk", "somon", "levrek", "hamsi"]):
        return MalzemeKategorisi.ET_TAVUK_BALIK
    
    # Süt Ürünleri
    if any(kelime in malzeme_adi_lower for kelime in ["süt", "yoğurt", "peynir", "kaşar", "tereyağ", "krema", "ayran", "kefir"]):
        return MalzemeKategorisi.SUT_URUNLERI
    
    # Tahıl & Baklagil
    if any(kelime in malzeme_adi_lower for kelime in ["ekmek", "un", "pirinç", "makarna", "bulgur", "nohut", "mercimek", "fasulye", "yulaf"]):
        return MalzemeKategorisi.TAHIL_BAKLAGIL
    
    # Şarküteri
    if any(kelime in malzeme_adi_lower for kelime in ["salam", "jambon", "pastırma"]):
        return MalzemeKategorisi.SARKUTERI
    
    # İçecek
    if any(kelime in malzeme_adi_lower for kelime in ["su", "meyve suyu", "kola", "gazoz", "çay", "kahve", "limonata"]):
        return MalzemeKategorisi.ICECEK
    
    # Temizlik
    if any(kelime in malzeme_adi_lower for kelime in ["deterjan", "çamaşır", "bulaşık", "temizlik", "sabun"]):
        return MalzemeKategorisi.TEMIZLIK
    
    # Kişisel Bakım
    if any(kelime in malzeme_adi_lower for kelime in ["şampuan", "diş macunu", "krem", "parfüm"]):
        return MalzemeKategorisi.KISISEL_BAKIM
    
    # Default
    return MalzemeKategorisi.DIGER
