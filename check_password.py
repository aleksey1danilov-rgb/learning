from app.core.database import SessionLocal
from app.models.user import User
from app.core.auth import verify_password

db = SessionLocal()
user = db.query(User).filter(User.username == 'admin').first()

if user:
    print(f'Пользователь найден: {user.username}')
    print(f'Email: {user.email}')
    print(f'Роль: {user.role}')
    print(f'Hashed password: {user.hashed_password[:30]}...')
    
    test_password = 'admin123'
    is_valid = verify_password(test_password, user.hashed_password)
    print(f'Пароль "{test_password}" правильный: {is_valid}')
else:
    print('Пользователь не найден')

db.close()
