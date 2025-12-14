"""
Database Migration - Weekly Menu Planning Tables (FIXED)
Haftalık menü planlama tablolarını ekler

✅ FIX: Tüm modelleri import ederek tablo bağımlılıklarını çözer

Çalıştırma:
cd backend
python add_menu_planning_tables_fixed.py
"""
import sys
import os

# Backend path'i ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from app.database import SQLALCHEMY_DATABASE_URL, Base

print("🔧 Menu Planning Tables Migration (FIXED)")
print("=" * 60)

# ✅ TÜM modelleri import et (sıra önemli!)
print("\n📦 Modeller import ediliyor...")

try:
    # 1. Temel modeller
    from app.models.user import User
    print("  ✅ User model loaded")
except Exception as e:
    print(f"  ⚠️ User model: {e}")

try:
    # 2. Recipe/Tarif modeli (varsa)
    try:
        from app.models.tarif import FavoriTarif
        print("  ✅ Recipe model loaded")
    except ImportError:
        try:
            from app.models.tarif import Tarif
            print("  ✅ Tarif model loaded")
        except ImportError:
            print("  ⚠️ Recipe/Tarif model not found")
except Exception as e:
    print(f"  ⚠️ Recipe model: {e}")

try:
    # 3. Diğer modeller
    from app.models.malzeme import Malzeme
    print("  ✅ Malzeme model loaded")
except Exception as e:
    print(f"  ⚠️ Malzeme model: {e}")

try:
    from app.models.alisveris import AlisverisListesi
    print("  ✅ AlisverisListesi model loaded")
except Exception as e:
    print(f"  ⚠️ AlisverisListesi model: {e}")

# 4. YENİ: Menu planning modelleri
from app.models.menu_plan import WeeklyMenuPlan, MenuItem, MenuShoppingListItem
print("  ✅ Menu planning models loaded")

print("\n" + "=" * 60)

# Engine oluştur
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
inspector = inspect(engine)

# Mevcut tabloları kontrol et
existing_tables = inspector.get_table_names()
print(f"\n📋 Mevcut tablolar ({len(existing_tables)}):")
for table in existing_tables:
    print(f"  - {table}")

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

# Kullanıcıya onay sor
response = input("\nDevam edilsin mi? (E/H): ")
if response.lower() not in ['e', 'evet', 'y', 'yes']:
    print("❌ Migration iptal edildi.")
    sys.exit(0)

try:
    # ✅ Tabloları oluştur - Base.metadata tüm modelleri bilir
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
            for col in columns[:8]:  # İlk 8 kolonu göster
                col_type = str(col['type'])
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                print(f"       - {col['name']}: {col_type} {nullable}")
            if len(columns) > 8:
                print(f"       ... ve {len(columns) - 8} kolon daha")

            # Foreign key'leri göster
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print(f"     Foreign Keys:")
                for fk in fks:
                    print(f"       - {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")

    print("\n" + "=" * 60)
    print("✅ Migration tamamlandı!")
    print("\nSonraki adımlar:")
    print("  1. ✅ User model - menu_plans ilişkisi zaten var")
    print("  2. ⚠️  Recipe/Tarif model - menu_items ilişkisi ekle:")
    print("       menu_items = relationship('MenuItem', back_populates='recipe')")
    print("\n  3. Backend'i restart et")
    print("  4. Test et:")
    print("       python")
    print("       >>> from app.models.menu_plan import WeeklyMenuPlan")
    print("       >>> from app.database import SessionLocal")
    print("       >>> db = SessionLocal()")
    print("       >>> menus = db.query(WeeklyMenuPlan).all()")
    print("       >>> print(f'Menüler: {len(menus)}')")

except Exception as e:
    print(f"\n❌ Migration hatası: {e}")
    print("\nDetaylı hata:")
    import traceback
    traceback.print_exc()

    print("\n💡 Çözüm önerileri:")
    print("  1. users tablosu var mı kontrol et:")
    print("     python")
    print("     >>> from app.database import engine")
    print("     >>> from sqlalchemy import inspect")
    print("     >>> print(inspect(engine).get_table_names())")
    print("\n  2. Tüm modeller doğru import ediliyor mu kontrol et")
    print("\n  3. app/models/__init__.py dosyasını kontrol et")

    sys.exit(1)