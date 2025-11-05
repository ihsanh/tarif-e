"""
Database Migration - Add Users Table (Fixed)
"""
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "tarif.db"

def migrate():
    """Users tablosunu ekle"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Önce tüm tabloları listele
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print("📋 Mevcut tablolar:", existing_tables)

        # Users tablosu var mı kontrol et
        if 'users' not in existing_tables:
            print("\n✅ Users tablosu oluşturuluyor...")
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    is_active BOOLEAN DEFAULT 1,
                    is_superuser BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

            # Index'ler oluştur
            cursor.execute("CREATE INDEX idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX idx_users_username ON users(username)")

            conn.commit()
            print("✅ Users tablosu başarıyla oluşturuldu!")
        else:
            print("\nℹ️ Users tablosu zaten mevcut")

            # Kolonları kontrol et
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"   Mevcut kolonlar: {columns}")

            # Eksik kolon varsa ekle
            required_columns = {
                'full_name': 'VARCHAR(255)',
                'is_active': 'BOOLEAN DEFAULT 1',
                'is_superuser': 'BOOLEAN DEFAULT 0',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            }

            for col_name, col_type in required_columns.items():
                if col_name not in columns:
                    print(f"   ➕ {col_name} kolonu ekleniyor...")
                    try:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                        conn.commit()
                        print(f"   ✅ {col_name} eklendi")
                    except sqlite3.OperationalError as e:
                        print(f"   ⚠️ {col_name} eklenemedi: {e}")

        # Tablo sayılarını göster (sadece var olan tablolar için)
        print("\n📊 Tablo istatistikleri:")

        for table_name in existing_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   {table_name}: {count} kayıt")
            except Exception as e:
                print(f"   {table_name}: Okunamadı ({e})")

        print("\n✅ Migration tamamlandı!")
        print("\n💡 Not: Backend'i yeniden başlatın:")
        print("   python -m uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("🔄 Users Tablosu Migration")
    print("=" * 50)
    migrate()