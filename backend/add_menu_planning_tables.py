"""
Database Migration - Weekly Menu Planning Tables
Haftalık menü planlama tablolarını ekler

Çalıştırma:
cd backend
python add_menu_planning_tables.py
"""
import sys
import os

# Backend path'i ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from app.database import SQLALCHEMY_DATABASE_URL, Base

# Models'i import et
from app.models.user import User
from app.models.recipe import Recipe
from app.models.menu_plan import WeeklyMenuPlan, MenuItem, MenuShoppingListItem

print("🔧 Menu Planning Tables Migration")
print("=" * 60)

# Engine oluştur
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
inspector = inspect(engine)

# Mevcut tabloları kontrol et
existing_tables = inspector.get_table_names()
print(f"📋 Mevcut tablolar: {existing_tables}")

# Yeni tablolar
new_tables = ["weekly_menu_plans", "menu_items", "menu_shopping_list_items"]

print("\n🔍 Kontrol ediliyor...")
tables_to_create = []

for table_name in new_tables:
    if table_name in existing_tables:
        print(f"  ✅ {table_name} - zaten var")
    else:
        print(f"  ➕ {table_name} - oluşturulacak")
        tables_to_create.append(table_name)

if not tables_to_create:
    print("\n✅ Tüm tablolar zaten mevcut! Migration gerekli değil.")
    sys.exit(0)

print(f"\n🚀 {len(tables_to_create)} tablo oluşturulacak...")

try:
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)
    
    print("\n✅ Migration başarılı!")
    print("\nOluşturulan tablolar:")
    
    # Yeni tabloları doğrula
    inspector = inspect(engine)
    for table_name in new_tables:
        if table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            print(f"\n  📊 {table_name}")
            print(f"     Kolonlar: {len(columns)}")
            for col in columns[:5]:  # İlk 5 kolonu göster
                print(f"       - {col['name']}: {col['type']}")
            if len(columns) > 5:
                print(f"       ... ve {len(columns) - 5} kolon daha")
    
    print("\n" + "=" * 60)
    print("✅ Migration tamamlandı!")
    print("\nSonraki adım:")
    print("  1. User model'e ilişki ekle:")
    print("     menu_plans = relationship('WeeklyMenuPlan', back_populates='user')")
    print("\n  2. Recipe model'e ilişki ekle:")
    print("     menu_items = relationship('MenuItem', back_populates='recipe')")
    print("\n  3. Backend'i restart et")
    
except Exception as e:
    print(f"\n❌ Migration hatası: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
