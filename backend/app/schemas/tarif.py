"""
Tarif Schemas
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional


class TarifOner(BaseModel):
    """Tarif önerme request"""
    malzemeler: List[str] = Field(..., min_items=1, description="En az 1 malzeme gerekli")
    sure: Optional[int] = Field(None, gt=0, le=1440, description="Süre dakika cinsinden")
    zorluk: Optional[str] = Field(None, pattern="^(kolay|orta|zor)$")
    kategori: Optional[str] = None

    @validator('malzemeler')
    def malzemeler_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('En az 1 malzeme gerekli')
        return v


class TarifFavori(BaseModel):
    """Favoriye ekleme request"""
    tarif: dict

    @validator('tarif')
    def tarif_must_have_baslik(cls, v):
        """Tarif en azından başlık içermeli"""
        if not v.get('baslik'):
            raise ValueError('Tarif başlığı gerekli')
        return v