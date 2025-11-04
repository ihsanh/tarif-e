"""
Malzeme Schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class MalzemeEkle(BaseModel):
    """Malzeme ekleme request"""
    name: str = Field(..., min_length=1, max_length=100, description="Malzeme adı")
    miktar: Optional[float] = Field(default=1.0, gt=0, description="Miktar (pozitif olmalı)")
    birim: Optional[str] = Field(default="adet", min_length=1, max_length=20)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        """İsim boş veya sadece boşluk olamaz"""
        if not v or not v.strip():
            raise ValueError('Malzeme adı boş olamaz')
        return v.strip().lower()

    @validator('miktar')
    def miktar_must_be_positive(cls, v):
        """Miktar pozitif olmalı"""
        if v <= 0:
            raise ValueError('Miktar 0\'dan büyük olmalı')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "domates",
                "miktar": 5,
                "birim": "adet"
            }
        }


class MalzemeGuncelle(BaseModel):
    """Malzeme güncelleme request"""
    miktar: float = Field(..., gt=0, description="Miktar (pozitif olmalı)")
    birim: str = Field(..., min_length=1, max_length=20)

    @validator('miktar')
    def miktar_must_be_positive(cls, v):
        """Miktar pozitif olmalı"""
        if v <= 0:
            raise ValueError('Miktar 0\'dan büyük olmalı')
        return v