"""
Alışveriş Schemas
"""
from pydantic import BaseModel, Field, validator
from typing import List


class AlisverisOlustur(BaseModel):
    """Alışveriş listesi oluşturma request"""
    malzemeler: List[str] = Field(..., min_items=1, description="En az 1 malzeme gerekli")

    @validator('malzemeler')
    def malzemeler_not_empty(cls, v):
        """Malzemeler boş olamaz"""
        if not v or len(v) == 0:
            raise ValueError('En az 1 malzeme gerekli')
        return v


class AlisverisUrunEkle(BaseModel):
    """Alışveriş listesine ürün ekleme request"""
    malzeme_adi: str = Field(..., min_length=1)
    miktar: float = Field(..., gt=0)
    birim: str = Field(..., min_length=1)

    @validator('malzeme_adi')
    def malzeme_adi_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Malzeme adı boş olamaz')
        return v.strip().lower()


class AlisverisUrunDurum(BaseModel):
    """Alışveriş ürün durumu güncelleme"""
    alinma_durumu: bool