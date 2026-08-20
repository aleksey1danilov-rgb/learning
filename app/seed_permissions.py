"""Заполнение таблицы permissions начальными данными"""
from app.core.database import SessionLocal
from app.models.permission import Permission

PERMISSIONS = [
    # Категория: courses
    {"code": "courses.create", "name": "Создание курсов", "description": "Позволяет создавать новые курсы", "category": "courses", "is_default": False},
    {"code": "courses.edit", "name": "Редактирование курсов", "description": "Позволяет редактировать существующие курсы", "category": "courses", "is_default": False},
    {"code": "courses.view_all", "name": "Просмотр всех курсов", "description": "Позволяет видеть все курсы платформы", "category": "courses", "is_default": False},
    {"code": "courses.view_assigned", "name": "Просмотр назначенных курсов", "description": "Позволяет видеть назначенные курсы", "category": "courses", "is_default": True},
    {"code": "courses.export", "name": "Экспорт курсов", "description": "Позволяет выгружать результаты в Excel", "category": "courses", "is_default": False},
    
    # Категория: calendar
    {"code": "calendar.view", "name": "Просмотр календаря", "description": "Позволяет просматривать календарь", "category": "calendar", "is_default": True},
    {"code": "calendar.edit", "name": "Редактирование календаря", "description": "Позволяет создавать и редактировать события", "category": "calendar", "is_default": False},
    
    # Категория: users
    {"code": "users.view", "name": "Просмотр сотрудников", "description": "Позволяет просматривать список сотрудников", "category": "users", "is_default": False},
    {"code": "users.edit", "name": "Редактирование сотрудников", "description": "Позволяет создавать и редактировать сотрудников", "category": "users", "is_default": False},
    {"code": "users.delete", "name": "Удаление сотрудников", "description": "Позволяет удалять сотрудников", "category": "users", "is_default": False},
    
    # Категория: roles
    {"code": "roles.manage", "name": "Управление ролями", "description": "Позволяет управлять ролями пользователей", "category": "roles", "is_default": False},
    {"code": "access.manage", "name": "Управление доступами", "description": "Позволяет управлять правами доступа", "category": "access", "is_default": False},
]

def seed_permissions():
    db = SessionLocal()
    try:
        for perm_data in PERMISSIONS:
            existing = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
            if not existing:
                perm = Permission(**perm_data)
                db.add(perm)
        db.commit()
        print(f"✅ Добавлено прав: {len(PERMISSIONS)}")
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_permissions()