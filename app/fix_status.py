from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()

# Показываем всех пользователей
users = db.query(User).all()
print("=== ВСЕ ПОЛЬЗОВАТЕЛИ ===")
for user in users:
    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}, Status: {user.registration_status}")

# Меняем статус для админа (обычно это первый пользователь)
admin = db.query(User).filter(User.role == "admin").first()
if admin:
    print(f"\nМеняем статус для админа: {admin.email}")
    admin.registration_status = "active"
    db.commit()
    print(f"✅ Статус изменен на: {admin.registration_status}")
else:
    print("\n❌ Админ не найден")

db.close()