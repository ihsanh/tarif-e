"""
Weekly Menu Plan Schemas
Pydantic schemas for menu planning
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# Enums
class MealTypeEnum(str, Enum):
    """Öğün tipleri"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class IngredientCategoryEnum(str, Enum):
    """Malzeme kategorileri"""
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    MEAT = "meat"
    FISH = "fish"
    DAIRY = "dairy"
    GRAINS = "grains"
    SPICES = "spices"
    OILS = "oils"
    BEVERAGES = "beverages"
    OTHER = "other"


class DayOfWeekEnum(int, Enum):
    """Haftanın günleri"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


# ============================================================
# MENU ITEM SCHEMAS
# ============================================================

class MenuItemBase(BaseModel):
    """Menu Item - Base Schema"""
    recipe_id: int = Field(..., gt=0, description="Tarif ID")
    day_of_week: int = Field(..., ge=0, le=6, description="Gün (0=Pazartesi, 6=Pazar)")
    meal_type: MealTypeEnum
    portions: int = Field(default=1, gt=0, description="Porsiyon sayısı")
    notes: Optional[str] = Field(None, max_length=500)


class MenuItemCreate(MenuItemBase):
    """Menu Item - Create"""
    pass


class MenuItemUpdate(BaseModel):
    """Menu Item - Update"""
    recipe_id: Optional[int] = Field(None, gt=0)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    meal_type: Optional[MealTypeEnum] = None
    portions: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None
    is_completed: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    """Menu Item - Response"""
    id: int
    menu_plan_id: int
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    
    # Recipe bilgileri (nested)
    recipe_name: Optional[str] = None
    recipe_image: Optional[str] = None
    recipe_prep_time: Optional[int] = None
    
    class Config:
        from_attributes = True


# ============================================================
# SHOPPING LIST SCHEMAS
# ============================================================

class ShoppingListItemBase(BaseModel):
    """Shopping List Item - Base"""
    ingredient_name: str = Field(..., min_length=1, max_length=200)
    total_amount: str = Field(..., min_length=1, max_length=100)
    unit: str = Field(..., min_length=1, max_length=50)
    category: IngredientCategoryEnum = IngredientCategoryEnum.OTHER
    notes: Optional[str] = None


class ShoppingListItemCreate(ShoppingListItemBase):
    """Shopping List Item - Create"""
    pass


class ShoppingListItemUpdate(BaseModel):
    """Shopping List Item - Update"""
    is_purchased: Optional[bool] = None
    is_in_stock: Optional[bool] = None
    notes: Optional[str] = None


class ShoppingListItemResponse(ShoppingListItemBase):
    """Shopping List Item - Response"""
    id: int
    menu_plan_id: int
    is_purchased: bool
    is_in_stock: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# WEEKLY MENU PLAN SCHEMAS
# ============================================================

class WeeklyMenuPlanBase(BaseModel):
    """Weekly Menu Plan - Base Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Menü adı")
    description: Optional[str] = Field(None, max_length=1000)
    week_start_date: date = Field(..., description="Hafta başlangıcı (Pazartesi)")
    week_end_date: date = Field(..., description="Hafta bitişi (Pazar)")
    
    @validator('week_end_date')
    def validate_week_dates(cls, v, values):
        """Hafta tarihleri kontrolü"""
        if 'week_start_date' in values:
            week_start = values['week_start_date']
            # Pazartesi-Pazar aralığı 6 gün olmalı
            if (v - week_start).days != 6:
                raise ValueError("Hafta 7 gün olmalı (Pazartesi-Pazar)")
        return v


class WeeklyMenuPlanCreate(WeeklyMenuPlanBase):
    """Weekly Menu Plan - Create"""
    is_active: bool = Field(default=True)


class WeeklyMenuPlanUpdate(BaseModel):
    """Weekly Menu Plan - Update"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WeeklyMenuPlanResponse(WeeklyMenuPlanBase):
    """Weekly Menu Plan - Response"""
    id: int
    user_id: int
    is_active: bool
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime
    
    # İlişkili veriler (opsiyonel)
    menu_items: List[MenuItemResponse] = []
    shopping_list_items: List[ShoppingListItemResponse] = []
    
    class Config:
        from_attributes = True


class WeeklyMenuPlanSummary(BaseModel):
    """Weekly Menu Plan - Summary (liste için)"""
    id: int
    name: str
    week_start_date: date
    week_end_date: date
    is_active: bool
    is_ai_generated: bool
    total_recipes: int = 0
    total_shopping_items: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# NUTRITION SUMMARY SCHEMAS
# ============================================================

class DailyNutritionSummary(BaseModel):
    """Günlük besin değerleri özeti"""
    day_of_week: int
    day_name: str
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    meal_count: int


class WeeklyNutritionSummary(BaseModel):
    """Haftalık besin değerleri özeti"""
    menu_plan_id: int
    daily_summaries: List[DailyNutritionSummary]
    
    # Haftalık toplamlar
    weekly_total_calories: float
    weekly_avg_calories: float
    weekly_total_protein: float
    weekly_total_carbs: float
    weekly_total_fat: float
    
    # Hedef karşılaştırması (eğer kullanıcı hedef belirlemiş ise)
    daily_calorie_goal: Optional[float] = None
    goal_achievement_percentage: Optional[float] = None


# ============================================================
# AI GENERATION SCHEMAS
# ============================================================

class AIMenuGenerationRequest(BaseModel):
    """AI ile menü oluşturma isteği"""
    week_start_date: date
    preferences: Optional[List[str]] = Field(
        default=[],
        description="Kullanıcı tercihleri (vegan, glutensiz, vb.)"
    )
    excluded_ingredients: Optional[List[str]] = Field(
        default=[],
        description="İstenmeyen malzemeler"
    )
    daily_calorie_target: Optional[int] = Field(
        None,
        ge=1000,
        le=5000,
        description="Günlük kalori hedefi"
    )
    meal_types: List[MealTypeEnum] = Field(
        default=[MealTypeEnum.BREAKFAST, MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        description="Hangi öğünler planlanacak"
    )


class AIMenuGenerationResponse(BaseModel):
    """AI menü oluşturma yanıtı"""
    success: bool
    menu_plan_id: Optional[int] = None
    message: str
    suggestions_count: int = 0
