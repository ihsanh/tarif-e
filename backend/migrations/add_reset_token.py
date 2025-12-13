# backend/migrations/add_reset_token.py
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(255)"))
    conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires DATETIME"))
    conn.commit()

print("✅ Migration completed")