"""
Tarif Schemas
"""
from pydantic import BaseModel
from typing import List, Optional


class TarifOner(BaseModel):
    """Tarif önerme request"""
    malzemeler: List[str]
    sure: Optional[int] = None
    zorluk: Optional[str] = None
    kategori: Optional[str] = None


class TarifFavori(BaseModel):
    """Favoriye ekleme request"""
    tarif: dict
