"""
Weekly Menu Plan Models
Haftalık menü planlama için database modelleri
✅ UPDATED: favori_tarifler tablosu ile entegrasyon
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class MealType(str, enum.Enum):
    """Öğün tipleri"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class IngredientCategory(str, enum.Enum):
    """Malzeme kategorileri - alışveriş listesi için"""
    VEGETABLES = "vegetables"  # Sebzeler
    FRUITS = "fruits"  # Meyveler
    MEAT = "meat"  # Et/Tavuk
    FISH = "fish"  # Balık/Deniz ürünleri
    DAIRY = "dairy"  # Süt ürünleri
    GRAINS = "grains"  # Tahıllar/Baklagiller
    SPICES = "spices"  # Baharatlar
    OILS = "oils"  # Yağlar
    BEVERAGES = "beverages"  # İçecekler
    OTHER = "other"  # Diğer


class WeeklyMenuPlan(Base):
    """
    Haftalık menü planı
    Bir kullanıcının bir hafta için oluşturduğu menü
    """
    __tablename__ = "weekly_menu_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Tarih bilgileri
    week_start_date = Column(Date, nullable=False)  # Pazartesi
    week_end_date = Column(Date, nullable=False)    # Pazar

    # Menü bilgileri
    name = Column(String(200), nullable=False)  # "15-21 Ocak Menüsü"
    description = Column(Text, nullable=True)   # Kullanıcı notu

    # Durum
    is_active = Column(Boolean, default=True)   # Aktif menü mi?
    is_ai_generated = Column(Boolean, default=False)  # AI ile mi oluşturuldu?

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="menu_plans")
    menu_items = relationship("MenuItem", back_populates="menu_plan", cascade="all, delete-orphan")
    shopping_list_items = relationship("MenuShoppingListItem", back_populates="menu_plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WeeklyMenuPlan {self.name} (User: {self.user_id})>"


class MenuItem(Base):
    """
    Menü öğesi - Belirli bir gün ve öğün için tarif
    Örnek: Pazartesi Kahvaltı - Menemen (2 porsiyon)

    ✅ favori_tarifler tablosu ile ilişkili
    """
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    menu_plan_id = Column(Integer, ForeignKey("weekly_menu_plans.id"), nullable=False)

    # ✅ DÜZELTME: favori_tarifler tablosuna bağlı
    tarif_id = Column(Integer, ForeignKey("favori_tarifler.id"), nullable=True)

    # Gün ve öğün bilgisi
    day_of_week = Column(Integer, nullable=False)  # 0=Pazartesi, 6=Pazar
    meal_type = Column(SQLEnum(MealType), nullable=False)

    # Porsiyon ve notlar
    portions = Column(Integer, default=1)  # Kaç porsiyon yapılacak
    notes = Column(Text, nullable=True)    # Kullanıcı notu (örn: "Misafir için 2 kat yap")

    # Durum
    is_completed = Column(Boolean, default=False)  # Yapıldı mı?
    completed_at = Column(DateTime, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    menu_plan = relationship("WeeklyMenuPlan", back_populates="menu_items")

    # ✅ FavoriTarif ile ilişki
    tarif = relationship("FavoriTarif", back_populates="menu_items")

    def __repr__(self):
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        return f"<MenuItem {days[self.day_of_week]} {self.meal_type.value} - Tarif: {self.tarif_id}>"


class MenuShoppingListItem(Base):
    """
    Menü alışveriş listesi öğesi
    Tüm haftanın malzemelerini toplar
    """
    __tablename__ = "menu_shopping_list_items"

    id = Column(Integer, primary_key=True, index=True)
    menu_plan_id = Column(Integer, ForeignKey("weekly_menu_plans.id"), nullable=False)

    # Malzeme bilgileri
    ingredient_name = Column(String(200), nullable=False)
    total_amount = Column(String(100), nullable=False)  # "500" veya "2.5"
    unit = Column(String(50), nullable=False)  # "gram", "adet", "su bardağı"

    # Kategori
    category = Column(SQLEnum(IngredientCategory), default=IngredientCategory.OTHER)

    # Durum
    is_purchased = Column(Boolean, default=False)  # Satın alındı mı?
    is_in_stock = Column(Boolean, default=False)   # Evde var mı?

    # Notlar
    notes = Column(Text, nullable=True)  # "Organik tercih et"

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    menu_plan = relationship("WeeklyMenuPlan", back_populates="shopping_list_items")

    def __repr__(self):
        return f"<ShoppingListItem {self.ingredient_name} - {self.total_amount} {self.unit}>"


"""
✅ FavoriTarif modeline eklenecek (app/models/favori_tarif.py veya benzer):

class FavoriTarif(Base):
    __tablename__ = "favori_tarifler"
    
    # ... mevcut kolonlar ...
    
    # İLİŞKİLER
    # ... mevcut ilişkiler ...
    
    # ✅ YENİ: Menu planning ilişkisi
    menu_items = relationship("MenuItem", back_populates="tarif")
"""
