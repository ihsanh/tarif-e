"""
Nutrition Model (OPSIYONEL)
backend/app/models/nutrition.py

NOT: Bu sadece besin değerlerini database'e kaydetmek istersen gerekli.
Şu an API direkt hesaplama yapıyor, kaydetmiyor.
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, JSON
from datetime import datetime
from .base import Base


class RecipeNutrition(Base):
    """Tarif besin değerleri (cache için)"""
    __tablename__ = "recipe_nutritions"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("favoriler.id"), unique=True)
    portions = Column(Integer, default=4)
    
    # Porsiyon başına
    calories_per_serving = Column(Float, nullable=False)
    protein_per_serving = Column(Float, nullable=False)
    carbs_per_serving = Column(Float, nullable=False)
    fat_per_serving = Column(Float, nullable=False)
    fiber_per_serving = Column(Float, nullable=True)
    sugar_per_serving = Column(Float, nullable=True)
    sodium_per_serving = Column(Float, nullable=True)
    cholesterol_per_serving = Column(Float, nullable=True)
    saturated_fat_per_serving = Column(Float, nullable=True)
    trans_fat_per_serving = Column(Float, nullable=True)
    
    # Toplam
    total_calories = Column(Float, nullable=False)
    total_protein = Column(Float, nullable=False)
    total_carbs = Column(Float, nullable=False)
    total_fat = Column(Float, nullable=False)
    
    # Meta
    calculated_at = Column(DateTime, default=datetime.now)
    calculation_source = Column(String(50), default="ai")
    raw_data = Column(JSON, nullable=True)
    
    # İlişki (eğer Favori modeline relationship eklemek istersen)
    # recipe = relationship("Favori", back_populates="nutrition")
    
    def to_dict(self):
        """Dict'e çevir"""
        return {
            "portions": self.portions,
            "per_serving": {
                "calories": round(self.calories_per_serving, 1),
                "protein": round(self.protein_per_serving, 1),
                "carbs": round(self.carbs_per_serving, 1),
                "fat": round(self.fat_per_serving, 1),
                "fiber": round(self.fiber_per_serving or 0, 1),
                "sugar": round(self.sugar_per_serving or 0, 1),
                "sodium": round(self.sodium_per_serving or 0, 1),
                "cholesterol": round(self.cholesterol_per_serving or 0, 1),
                "saturated_fat": round(self.saturated_fat_per_serving or 0, 1),
                "trans_fat": round(self.trans_fat_per_serving or 0, 1),
            },
            "total": {
                "calories": round(self.total_calories, 1),
                "protein": round(self.total_protein, 1),
                "carbs": round(self.total_carbs, 1),
                "fat": round(self.total_fat, 1),
            },
            "source": self.calculation_source,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None
        }


# ============================================
# EĞER KAYDETME ÖZELLİĞİ İSTERSEN:
# backend/app/routes/tarif.py'ye bu endpoint'i ekle
# ============================================

"""
@router.post("/favoriler/{favori_id}/nutrition")
async def save_nutrition_to_favorite(
    favori_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Favoriyi al
    favori = db.query(Favori).filter(
        Favori.id == favori_id,
        Favori.user_id == current_user.id
    ).first()
    
    if not favori:
        raise HTTPException(status_code=404, detail="Favori bulunamadı")
    
    # Zaten hesaplanmış mı?
    existing = db.query(RecipeNutrition).filter(
        RecipeNutrition.recipe_id == favori_id
    ).first()
    
    if existing:
        return {
            "success": True,
            "message": "Besin değerleri zaten mevcut",
            "nutrition": existing.to_dict()
        }
    
    # Malzemeleri parse et
    import json
    if isinstance(favori.malzemeler, str):
        malzemeler = json.loads(favori.malzemeler)
    else:
        malzemeler = favori.malzemeler
    
    # Besin değerlerini hesapla
    nutrition_data = await ai_service.calculate_nutrition(
        recipe_title=favori.baslik,
        ingredients=malzemeler,
        portions=4
    )
    
    # Veritabanına kaydet
    nutrition = RecipeNutrition(
        recipe_id=favori_id,
        portions=4,
        calories_per_serving=nutrition_data["per_serving"]["calories"],
        protein_per_serving=nutrition_data["per_serving"]["protein"],
        carbs_per_serving=nutrition_data["per_serving"]["carbs"],
        fat_per_serving=nutrition_data["per_serving"]["fat"],
        fiber_per_serving=nutrition_data["per_serving"].get("fiber"),
        sugar_per_serving=nutrition_data["per_serving"].get("sugar"),
        sodium_per_serving=nutrition_data["per_serving"].get("sodium"),
        cholesterol_per_serving=nutrition_data["per_serving"].get("cholesterol"),
        saturated_fat_per_serving=nutrition_data["per_serving"].get("saturated_fat"),
        trans_fat_per_serving=nutrition_data["per_serving"].get("trans_fat"),
        total_calories=nutrition_data["total"]["calories"],
        total_protein=nutrition_data["total"]["protein"],
        total_carbs=nutrition_data["total"]["carbs"],
        total_fat=nutrition_data["total"]["fat"],
        calculation_source="ai",
        raw_data=nutrition_data
    )
    
    db.add(nutrition)
    db.commit()
    db.refresh(nutrition)
    
    return {
        "success": True,
        "message": "Besin değerleri hesaplandı ve kaydedildi",
        "nutrition": nutrition.to_dict()
    }
"""
