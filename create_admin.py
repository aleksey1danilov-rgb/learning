from app.core.database import SessionLocal
from app.models.user import User
from app.core.auth import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == "admin").first()

if not admin:
    admin = User(
        username="admin",
        email="admin@avito.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Administrator",
        role="admin",
        is_active=True,
        registration_status="active"
    )
    db.add(admin)
    db.commit()
    print("Admin created!")
    print("Email: admin@avito.com")
    print("Password: admin123")
else:
    print("Admin already exists")
    print(f"Email: {admin.email}")

db.close()