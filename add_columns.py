from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    # Добавляем колонки для 2FA
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN DEFAULT 0"))
        print("✅ is_2fa_enabled added")
    except Exception as e:
        print(f"⚠️ is_2fa_enabled: {e}")
    
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(100)"))
        print("✅ two_factor_secret added")
    except Exception as e:
        print(f"⚠️ two_factor_secret: {e}")
    
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN backup_codes TEXT"))
        print("✅ backup_codes added")
    except Exception as e:
        print(f"⚠️ backup_codes: {e}")
    
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN registration_status VARCHAR(20) DEFAULT 'pending'"))
        print("✅ registration_status added")
    except Exception as e:
        print(f"⚠️ registration_status: {e}")
    
    conn.commit()
    print("✅ All columns added!")