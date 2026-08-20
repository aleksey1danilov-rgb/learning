import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже админ
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing_admin:
            print(f"⚠️  Администратор уже существует: {existing_admin.email}")
            return
        
        # Создаём админа
        admin = User(
            username="admin",
            email="admin@avito.com",
            full_name="Администратор системы",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("=" * 50)
        print("✅ Администратор успешно создан!")
        print("=" * 50)
        print(f"📧 Email: admin@avito.com")
        print(f"🔑 Пароль: admin123")
        print(f"👤 Имя: {admin.full_name}")
        print(f"🎭 Роль: {admin.role.value}")
        print("=" * 50)
        print("⚠️  Не забудьте сменить пароль после первого входа!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()