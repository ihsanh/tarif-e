"""
Database Tablo Kontrolü
backend/check_tables.py
"""
import sqlite3
from pathlib import Path

# Database yolu
db_path = Path(__file__).parent / "../data" / "tarif_e.db"

print(f"📁 Database: {db_path}")
print(f"   Var mı? {db_path.exists()}\n")

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tüm tabloları listele
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print("📊 Mevcut Tablolar:")
    print("=" * 50)
    for table in tables:
        print(f"   ✅ {table[0]}")

        # Tablo yapısını göster
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"      - {col[1]} ({col[2]})")
        print()

    conn.close()
else:
    print("❌ Database dosyası bulunamadı!")
    print("   Konum:", db_path)