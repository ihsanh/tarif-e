"""
Database Tablolarını Oluştur
backend/create_tables.py
"""
import sys
from pathlib import Path

# Backend dizinini sys.path'e ekle
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import engine
from app.models import Base, User, Malzeme, KullaniciMalzeme, AlisverisListesi, AlisverisUrunu, ListePaylasim

print("🔨 Tablolar oluşturuluyor...")
print(f"📁 Database: {engine.url}\n")

try:
    # Tüm tabloları oluştur
    Base.metadata.create_all(bind=engine)

    print("✅ Tablolar başarıyla oluşturuldu!\n")

    # Oluşturulan tabloları listele
    print("📊 Oluşturulan tablolar:")
    for table in Base.metadata.sorted_tables:
        print(f"   ✅ {table.name}")
        for column in table.columns:
            print(f"      - {column.name} ({column.type})")
        print()

except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback

    traceback.print_exc()