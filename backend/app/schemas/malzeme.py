"""
Malzeme Schemas
"""
from pydantic import BaseModel
from typing import Optional


class MalzemeEkle(BaseModel):
    """Malzeme ekleme request"""
    name: str
    miktar: Optional[float] = 1.0
    birim: Optional[str] = "adet"


class MalzemeGuncelle(BaseModel):
    """Malzeme güncelleme request"""
    miktar: float
    birim: str
