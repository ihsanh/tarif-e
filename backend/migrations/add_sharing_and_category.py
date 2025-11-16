"""
Database Migration - Liste Paylaşma ve Kategori
backend/migrations/add_sharing_and_category.py

KULLANIM:
cd backend
python migrations/add_sharing_and_category.py
"""
import sys
import os
from pathlib import Path

# Backend dizinini sys.path'e ekle
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.models.base import Base  # Direkt base'den
from app.database import engine as app_engine

def run_migration():
    """Migration'ı çalıştır"""
    print("=" * 60)
    print("🔄 Migration başlıyor...")
    print("=" * 60)
    
    # Database yolunu göster
    db_url = str(app_engine.url)
    print(f"📁 Database: {db_url}")
    
    try:
        with app_engine.connect() as conn:
            # 1. Malzeme tablosuna kategori ekle
            print("\n1️⃣  Malzeme tablosuna 'kategori' kolonu ekleniyor...")
            try:
                conn.execute(text("""
                    ALTER TABLE malzeme 
                    ADD COLUMN kategori TEXT DEFAULT 'diğer'
                """))
                conn.commit()
                print("   ✅ Kategori kolonu eklendi")
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print("   ⚠️  Kategori kolonu zaten mevcut")
                else:
                    print(f"   ❌ Hata: {e}")
            
            # 2. Alışveriş ürünü tablosuna kategori ekle
            print("\n2️⃣  Alışveriş ürünü tablosuna 'kategori' kolonu ekleniyor...")
            try:
                conn.execute(text("""
                    ALTER TABLE alisveris_urunu 
                    ADD COLUMN kategori TEXT DEFAULT 'diğer'
                """))
                conn.commit()
                print("   ✅ Kategori kolonu eklendi")
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print("   ⚠️  Kategori kolonu zaten mevcut")
                else:
                    print(f"   ❌ Hata: {e}")
            
            # 3. Liste paylaşım tablosunu oluştur
            print("\n3️⃣  Liste paylaşım tablosu oluşturuluyor...")
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS liste_paylasim (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        liste_id INTEGER NOT NULL,
                        paylasan_user_id INTEGER NOT NULL,
                        paylasilan_user_id INTEGER NOT NULL,
                        rol TEXT DEFAULT 'view',
                        paylasim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        kabul_edildi BOOLEAN DEFAULT 0,
                        FOREIGN KEY (liste_id) REFERENCES alisveris_listesi(id) ON DELETE CASCADE,
                        FOREIGN KEY (paylasan_user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (paylasilan_user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                print("   ✅ Liste paylaşım tablosu oluşturuldu")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg:
                    print("   ⚠️  Liste paylaşım tablosu zaten mevcut")
                else:
                    print(f"   ❌ Hata: {e}")
            
            # 4. Tabloları kontrol et
            print("\n4️⃣  Tablolar kontrol ediliyor...")
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """))
            tables = [row[0] for row in result]
            print(f"   📊 Mevcut tablolar: {', '.join(tables)}")
            
            # 5. Yeni kolonları kontrol et
            print("\n5️⃣  Yeni kolonlar kontrol ediliyor...")
            
            # Malzeme tablosu
            result = conn.execute(text("PRAGMA table_info(malzeme)"))
            columns = [row[1] for row in result]
            if 'kategori' in columns:
                print("   ✅ malzeme.kategori mevcut")
            else:
                print("   ❌ malzeme.kategori bulunamadı!")
            
            # Alışveriş ürünü tablosu
            result = conn.execute(text("PRAGMA table_info(alisveris_urunu)"))
            columns = [row[1] for row in result]
            if 'kategori' in columns:
                print("   ✅ alisveris_urunu.kategori mevcut")
            else:
                print("   ❌ alisveris_urunu.kategori bulunamadı!")
            
            # Liste paylaşım tablosu
            if 'liste_paylasim' in tables:
                print("   ✅ liste_paylasim tablosu mevcut")
            else:
                print("   ❌ liste_paylasim tablosu bulunamadı!")
        
        print("\n" + "=" * 60)
        print("✅ Migration tamamlandı!")
        print("=" * 60)
        print("\n📋 Sıradaki adımlar:")
        print("1. ✅ models/malzeme.py'yi güncelle")
        print("2. ✅ models/alisveris.py'yi güncelle")
        print("3. ✅ models/__init__.py'yi güncelle")
        print("4. ✅ schemas/malzeme.py'yi güncelle")
        print("5. ✅ schemas/alisveris.py'yi güncelle")
        print("6. ✅ schemas/__init__.py'yi güncelle")
        print("7. ✅ routes/alisveris_extended.py'yi ekle")
        print("8. ✅ main.py'ye yeni router'ı ekle:")
        print("   from app.routes.alisveris_extended import router as alisveris_extended_router")
        print("   app.include_router(alisveris_extended_router)")
        print("9. 🔄 Backend'i yeniden başlat")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration hatası: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def rollback_migration():
    """Migration'ı geri al"""
    print("=" * 60)
    print("⏪ Migration geri alınıyor...")
    print("=" * 60)
    
    try:
        with app_engine.connect() as conn:
            # Paylaşım tablosunu sil
            print("\n1️⃣  liste_paylasim tablosu siliniyor...")
            conn.execute(text("DROP TABLE IF EXISTS liste_paylasim"))
            conn.commit()
            print("   ✅ Tablo silindi")
            
            # Not: SQLite ALTER TABLE DROP COLUMN desteklemiyor
            # Kategori kolonlarını kaldırmak için tablo yeniden oluşturulmalı
            print("\n⚠️  Not: SQLite'da kolon silme desteklenmez.")
            print("   Kategori kolonları tabloda kalacak.")
        
        print("\n✅ Rollback tamamlandı")
    except Exception as e:
        print(f"\n❌ Rollback hatası: {e}")
        return False
    
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_migration()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)
