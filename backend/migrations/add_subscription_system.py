"""
Database Migration - Add Subscription System
Creates subscriptions and usage_logs tables, and initializes all existing users with PRO subscription

Çalıştırma: python migrations/add_subscription_system.py
"""
import sys
import os

# Backend dizinini path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, SessionLocal
from app.models.user import User
from app.models.subscription import Subscription
from app.models.usage_log import UsageLog
from app.config import settings
from sqlalchemy import text, inspect
from datetime import datetime

def table_exists(table_name: str) -> bool:
    """Tablo var mı kontrol et"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def create_subscription_tables():
    """Subscription ve UsageLog tablolarını oluştur"""

    print("=" * 60)
    print("SUBSCRIPTION SYSTEM MIGRATION")
    print("=" * 60)

    print("\n[1/4] Tablolar kontrol ediliyor...")

    # Subscriptions tablosunu oluştur
    if not table_exists('subscriptions'):
        print("   [CREATE] subscriptions tablosu oluşturuluyor...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    tier VARCHAR(50) NOT NULL DEFAULT 'pro',
                    billing_cycle VARCHAR(50) NOT NULL DEFAULT 'monthly',
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_date DATETIME,
                    auto_renew BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            conn.commit()
        print("   [SUCCESS] subscriptions tablosu oluşturuldu")
    else:
        print("   [INFO] subscriptions tablosu zaten var")

    # UsageLogs tablosunu oluştur
    if not table_exists('usage_logs'):
        print("   [CREATE] usage_logs tablosu oluşturuluyor...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type VARCHAR(100) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))

            # İndeksler ekle (performans için)
            conn.execute(text("""
                CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_usage_logs_action_type ON usage_logs(action_type)
            """))
            conn.execute(text("""
                CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at)
            """))

            conn.commit()
        print("   [SUCCESS] usage_logs tablosu ve indeksler oluşturuldu")
    else:
        print("   [INFO] usage_logs tablosu zaten var")

def initialize_user_subscriptions():
    """Mevcut tüm kullanıcılara PRO abonelik ata"""

    print("\n[2/4] Mevcut kullanicilar icin abonelikler olusturuluyor...")

    db = SessionLocal()
    try:
        # Tum kullanıcilari getir
        users = db.query(User).all()
        print(f"   [INFO] Toplam {len(users)} kullanici bulundu")

        created_count = 0
        skipped_count = 0

        for user in users:
            # Kullanicinin aboneligi var mi kontrol et
            existing_subscription = db.query(Subscription).filter(
                Subscription.user_id == user.id
            ).first()

            if existing_subscription:
                print(f"   [SKIP] User {user.id} ({user.username}) - abonelik zaten var")
                skipped_count += 1
                continue

            # PRO abonelik olustur
            subscription = Subscription(
                user_id=user.id,
                tier="pro",
                billing_cycle="monthly",
                status="active",
                auto_renew=True
            )
            subscription.calculate_end_date()

            db.add(subscription)
            created_count += 1

            print(f"   [CREATE] User {user.id} ({user.username}) - PRO abonelik olusturuldu")

        db.commit()

        print(f"\n   [SUMMARY]")
        print(f"   - Olusturulan: {created_count}")
        print(f"   - Atlanan: {skipped_count}")
        print(f"   - Toplam: {len(users)}")

    except Exception as e:
        print(f"\n   [ERROR] Abonelik olusturma hatasi: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_migration():
    """Migration'in basarili olup olmadigini dogrula"""

    print("\n[3/4] Migration dogrulaniy or...")

    db = SessionLocal()
    try:
        # Kullanici sayisi
        user_count = db.query(User).count()
        print(f"   [INFO] Toplam kullanici: {user_count}")

        # Abonelik sayisi
        subscription_count = db.query(Subscription).count()
        print(f"   [INFO] Toplam abonelik: {subscription_count}")

        # PRO kullanici sayisi
        pro_count = db.query(Subscription).filter(
            Subscription.tier == "pro",
            Subscription.status == "active"
        ).count()
        print(f"   [INFO] Aktif PRO kullanici: {pro_count}")

        # Kullanim log sayisi
        usage_log_count = db.query(UsageLog).count()
        print(f"   [INFO] Toplam usage log: {usage_log_count}")

        # Her kullanicinin aboneligi var mi kontrol et
        if user_count == subscription_count:
            print(f"\n   [SUCCESS] Tum kullanicilarin aboneligi var!")
        else:
            print(f"\n   [WARNING] {user_count - subscription_count} kullanicinin aboneligi yok!")

    finally:
        db.close()

def show_config():
    """Abonelik yapilandirmasini goster"""

    print("\n[4/4] Abonelik yapilandirmasi:")
    print(f"   - Standart gunluk limit: {settings.STANDARD_DAILY_RECIPE_LIMIT} tarif/gun")
    print(f"   - PRO aylik ucret: {settings.PRO_MONTHLY_PRICE} TL")
    print(f"   - PRO yillik ucret: {settings.PRO_YEARLY_PRICE} TL")
    print(f"   - Varsayilan paket: {settings.DEFAULT_SUBSCRIPTION_TIER}")

def main():
    """Ana migration fonksiyonu"""
    try:
        create_subscription_tables()
        initialize_user_subscriptions()
        verify_migration()
        show_config()

        print("\n" + "=" * 60)
        print("[SUCCESS] MIGRATION TAMAMLANDI!")
        print("=" * 60)
        print("\nAbonelik sistemi basariyla kuruldu.")
        print("Tum mevcut kullanicilar PRO pakete sahip.")
        print("\nAPI Endpoints:")
        print("  - GET  /api/subscription/status")
        print("  - GET  /api/subscription/usage")
        print("  - POST /api/subscription/upgrade")
        print("  - GET  /api/subscription/pricing")
        print("  - GET  /api/profile/me (abonelik bilgisi dahil)")

    except Exception as e:
        print(f"\n[ERROR] Migration basarisiz: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
