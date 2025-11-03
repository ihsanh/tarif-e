"""
Alışveriş Schemas
"""
from pydantic import BaseModel
from typing import List


class AlisverisOlustur(BaseModel):
    """Alışveriş listesi oluşturma request"""
    malzemeler: List[str]


class AlisverisUrunEkle(BaseModel):
    """Alışveriş listesine ürün ekleme request"""
    malzeme_adi: str
    miktar: float
    birim: str


class AlisverisUrunDurum(BaseModel):
    """Alışveriş ürün durumu güncelleme"""
    alinma_durumu: bool
