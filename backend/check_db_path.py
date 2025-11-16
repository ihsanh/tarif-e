"""
Database Path Kontrolü
backend/check_db_path.py
"""
import os
import sys
from pathlib import Path

# Backend dizinini ekle
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("=" * 70)
print("📁 DATABASE PATH KONTROLÜ")
print("=" * 70)

# Test modu olmadan
os.environ["TESTING"] = "false"
from app.database import SQLALCHEMY_DATABASE_URL as PROD_URL, DB_PATH as PROD_PATH

print("\n✅ PRODUCTION MODE:")
print(f"   URL: {PROD_URL}")
print(f"   Path: {PROD_PATH}")
print(f"   Exists: {PROD_PATH.exists()}")

# Test modu ile
os.environ["TESTING"] = "true"

# Modülü yeniden yükle
import importlib
import app.database
importlib.reload(app.database)

from app.database import SQLALCHEMY_DATABASE_URL as TEST_URL, DB_PATH as TEST_PATH

print("\n⚠️  TEST MODE:")
print(f"   URL: {TEST_URL}")
print(f"   Path: {TEST_PATH}")
print(f"   Exists: {TEST_PATH.exists()}")

print("\n" + "=" * 70)
print("🔍 SONUÇ:")
if PROD_PATH == TEST_PATH:
    print("   ❌ PROBLEM: Production ve test aynı database kullanıyor!")
    print(f"      Her ikisi de: {PROD_PATH}")
else:
    print("   ✅ DOĞRU: Production ve test farklı database kullanıyor")
    print(f"      Production: {PROD_PATH}")
    print(f"      Test: {TEST_PATH}")
print("=" * 70)
