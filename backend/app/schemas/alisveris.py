"""
Alışveriş Schemas - Kategori ve Paylaşım Eklendi
backend/app/schemas/alisveris.py
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from pydantic.v1 import validator

from app.models.malzeme import MalzemeKategorisi
from app.models.alisveris import PaylaşımRolü


# ============================================
# ALIŞVERİŞ ÜRÜNÜ SCHEMAS
# ============================================

class AlisverisUrunuBase(BaseModel):
    """Alışveriş ürünü base"""
    malzeme_adi: str = Field(..., min_length=1, max_length=100)
    miktar: float = Field(gt=0)
    birim: str = Field(default="adet", max_length=20)
    kategori: Optional[MalzemeKategorisi] = MalzemeKategorisi.DIGER  # ✅ YENİ
    alinan: bool = False


class AlisverisUrunuCreate(AlisverisUrunuBase):
    """Ürün ekleme"""
    pass


class AlisverisUrunuUpdate(BaseModel):
    """Ürün güncelleme"""
    malzeme_adi: Optional[str] = None
    miktar: Optional[float] = Field(None, gt=0)
    birim: Optional[str] = None
    kategori: Optional[MalzemeKategorisi] = None  # ✅ YENİ
    alinan: Optional[bool] = None


class AlisverisUrunuResponse(AlisverisUrunuBase):
    """Ürün response"""
    id: int
    liste_id: int
    
    class Config:
        from_attributes = True


# ============================================
# LİSTE PAYLAŞMA SCHEMAS (YENİ)
# ============================================

class ListePaylasimCreate(BaseModel):
    """Liste paylaşma request"""
    liste_id: int = Field(..., gt=0)
    paylasilan_email_veya_username: str = Field(..., min_length=3)
    rol: PaylaşımRolü = PaylaşımRolü.GORUNTULEYEBILIR
    mesaj: Optional[str] = Field(None, max_length=500)  # Opsiyonel davet mesajı


class ListePaylasimUpdate(BaseModel):
    """Paylaşım güncelleme"""
    rol: Optional[PaylaşımRolü] = None
    kabul_edildi: Optional[bool] = None


class ListePaylasimResponse(BaseModel):
    """Paylaşım response"""
    id: int
    liste_id: int
    paylasan_user_id: int
    paylasilan_user_id: int
    paylasan_username: str  # Ekstra bilgi
    paylasilan_username: str  # Ekstra bilgi
    rol: PaylaşımRolü
    paylasim_tarihi: datetime
    kabul_edildi: bool
    
    class Config:
        from_attributes = True


class PaylasilanListeResponse(BaseModel):
    """Benimle paylaşılan liste"""
    liste_id: int
    liste_baslik: str
    paylasan_username: str
    rol: PaylaşımRolü
    paylasim_tarihi: datetime
    kabul_edildi: bool
    urun_sayisi: int


# ============================================
# ALIŞVERİŞ LİSTESİ SCHEMAS
# ============================================

class AlisverisListesiCreate(BaseModel):
    """Liste oluşturma"""
    baslik: str = Field(..., min_length=1, max_length=200)
    aciklama: Optional[str] = None
    malzemeler: List[str] = Field(..., min_items=1)  # ["domates - 2 kg", ...]

    @validator('malzemeler')
    def malzemeler_bos_olamaz(cls, v):
        if not v or len(v) == 0:
            raise ValueError('En az 1 malzeme eklemelisiniz')
        return v

class AlisverisListesiResponse(BaseModel):
    """Liste response"""
    id: int
    baslik: str
    aciklama: Optional[str]
    user_id: int
    olusturma_tarihi: datetime
    tamamlandi: bool
    tamamlanma_tarihi: Optional[datetime]
    urunler: List[AlisverisUrunuResponse]
    paylasilmalar: List[ListePaylasimResponse] = []  # ✅ YENİ
    
    class Config:
        from_attributes = True


# ============================================
# KATEGORİ GRUPLAMA SCHEMAS
# ============================================

class KategoriGrubu(BaseModel):
    """Kategoriye göre gruplu ürünler"""
    kategori: MalzemeKategorisi
    kategori_adi: str  # Türkçe ad
    urunler: List[AlisverisUrunuResponse]
    toplam_urun: int


class GrupluListeResponse(BaseModel):
    """Kategoriye göre gruplu liste"""
    liste_id: int
    liste_baslik: str
    kategoriler: List[KategoriGrubu]
    toplam_kategori: int
    toplam_urun: int


# ============================================
# HELPER FUNCTIONS
# ============================================

def kategori_turkce_adi(kategori: MalzemeKategorisi) -> str:
    """Kategori enum'ını Türkçe'ye çevir"""
    ceviri = {
        MalzemeKategorisi.MEYVE_SEBZE: "Meyve & Sebze",
        MalzemeKategorisi.ET_TAVUK_BALIK: "Et, Tavuk & Balık",
        MalzemeKategorisi.SUT_URUNLERI: "Süt Ürünleri",
        MalzemeKategorisi.TAHIL_BAKLAGIL: "Tahıl & Baklagil",
        MalzemeKategorisi.SARKUTERI: "Şarküteri",
        MalzemeKategorisi.DONUK_GIDA: "Donuk Gıda",
        MalzemeKategorisi.ATISTIRMALIK: "Atıştırmalık",
        MalzemeKategorisi.ICECEK: "İçecek",
        MalzemeKategorisi.TEMIZLIK: "Temizlik",
        MalzemeKategorisi.KISISEL_BAKIM: "Kişisel Bakım",
        MalzemeKategorisi.DIGER: "Diğer"
    }
    return ceviri.get(kategori, "Diğer")
