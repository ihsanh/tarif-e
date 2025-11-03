"""
Yardımcı Fonksiyonlar
"""
from datetime import datetime
from typing import Optional


def format_date(date: datetime, format: str = "%d.%m.%Y %H:%M") -> str:
    """Tarihi formatla"""
    return date.strftime(format)


def clean_string(text: str) -> str:
    """String'i temizle (boşluklar, küçük harf)"""
    return text.strip().lower()


def parse_malzeme_string(malzeme_str: str) -> dict:
    """
    Malzeme string'ini parse et
    
    Örnek: "domates - 3 adet" -> {"name": "domates", "miktar": 3, "birim": "adet"}
    """
    parts = malzeme_str.split('-')
    if len(parts) < 2:
        return {"name": malzeme_str.strip(), "miktar": 1, "birim": "adet"}
    
    name = parts[0].strip().lower()
    miktar_birim = parts[1].strip()
    
    miktar_parts = miktar_birim.split()
    try:
        miktar = float(miktar_parts[0]) if miktar_parts else 1
        birim = miktar_parts[1] if len(miktar_parts) > 1 else "adet"
    except:
        miktar = 1
        birim = "adet"
    
    return {
        "name": name,
        "miktar": miktar,
        "birim": birim
    }


def calculate_recipe_difficulty(ingredients_count: int, steps_count: int) -> str:
    """
    Tarif zorluğunu hesapla
    
    Args:
        ingredients_count: Malzeme sayısı
        steps_count: Adım sayısı
        
    Returns:
        str: kolay, orta, zor
    """
    total_complexity = ingredients_count + (steps_count * 2)
    
    if total_complexity <= 10:
        return "kolay"
    elif total_complexity <= 20:
        return "orta"
    else:
        return "zor"
