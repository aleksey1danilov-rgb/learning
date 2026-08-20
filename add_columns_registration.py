# add_columns_registration.py
from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    # Добавляем колонку temporary_password
    try:
        conn.execute(text("ALTER TABLE registration_requests ADD COLUMN temporary_password VARCHAR(200)"))
        print("✅ Колонка temporary_password добавлена")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("⚠️ Колонка temporary_password уже существует")
        else:
            print(f"❌ Ошибка при добавлении temporary_password: {e}")
    
    # Добавляем колонку temporary_password_plain
    try:
        conn.execute(text("ALTER TABLE registration_requests ADD COLUMN temporary_password_plain VARCHAR(50)"))
        print("✅ Колонка temporary_password_plain добавлена")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("⚠️ Колонка temporary_password_plain уже существует")
        else:
            print(f"❌ Ошибка при добавлении temporary_password_plain: {e}")
    
    conn.commit()
    print("✅ База данных обновлена!")