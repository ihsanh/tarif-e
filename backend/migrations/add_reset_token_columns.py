"""
Database Migration - Add Reset Token Columns
Çalıştırma: python add_reset_token_columns.py
"""
import sys
import os

# Backend dizinini path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from sqlalchemy import text, inspect

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Kolon var mı kontrol et"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_reset_token_columns():
    """Users tablosuna reset_token kolonlarını ekle"""
    
    print("🔍 Mevcut kolonlar kontrol ediliyor...")
    
    with engine.connect() as conn:
        # reset_token kolonu var mı?
        if not check_column_exists('users', 'reset_token'):
            print("➕ reset_token kolonu ekleniyor...")
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(255)"))
            print("   ✅ reset_token eklendi")
        else:
            print("   ℹ️  reset_token zaten var")
        
        # reset_token_expires kolonu var mı?
        if not check_column_exists('users', 'reset_token_expires'):
            print("➕ reset_token_expires kolonu ekleniyor...")
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires DATETIME"))
            print("   ✅ reset_token_expires eklendi")
        else:
            print("   ℹ️  reset_token_expires zaten var")
        
        conn.commit()
    
    print("\n✅ Migration tamamlandı!")
    print("\n📊 Users tablosu yapısı:")
    
    # Tablo yapısını göster
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(users)"))
        for row in result:
            print(f"   - {row[1]} ({row[2]})")

if __name__ == "__main__":
    try:
        add_reset_token_columns()
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        sys.exit(1)
