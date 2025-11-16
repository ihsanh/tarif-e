
# ============================================
# MALZEME SCHEMAS (Mevcut + Kategori)
# ============================================
from .malzeme import (
    MalzemeEkle,  # ✅ Mevcut
    MalzemeGuncelle,  # ✅ Mevcut
    MalzemeResponse  # ✅ YENİ
)

# ============================================
# ALIŞVERİŞ SCHEMAS (YENİ)
# ============================================
from .alisveris import (
    # Ürün schemas
    AlisverisUrunuCreate,
    AlisverisUrunuUpdate,
    AlisverisUrunuResponse,
    # Liste schemas
    AlisverisListesiCreate,
    AlisverisListesiResponse,
    # Paylaşım schemas
    ListePaylasimCreate,
    ListePaylasimUpdate,
    ListePaylasimResponse,
    PaylasilanListeResponse,
    # Kategori schemas
    KategoriGrubu,
    GrupluListeResponse,
    kategori_turkce_adi
)

from .user import UserRegister, UserLogin, UserResponse, Token
from .tarif import TarifOner, TarifFavori

__all__ = [
    # Malzeme
    "MalzemeEkle",
    "MalzemeGuncelle",
    "MalzemeResponse",
    "AlisverisUrunuCreate",
    "AlisverisUrunuUpdate",
    "AlisverisUrunuResponse",
    "AlisverisListesiCreate",
    "AlisverisListesiResponse",
    "ListePaylasimCreate",
    "ListePaylasimUpdate",
    "ListePaylasimResponse",
    "PaylasilanListeResponse",
    "KategoriGrubu",
    "GrupluListeResponse",
    "kategori_turkce_adi",
    "UserRegister",
    "UserLogin",
    "UserRegister",
    "UserResponse"
]