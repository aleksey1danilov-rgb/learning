from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import secrets
import pyotp
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import create_access_token, get_current_user, get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
import re
import dns.resolver

def validate_email(email):
    # Проверка формата
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Некорректный формат email"
    
    # Проверка MX-записи
    domain = email.split('@')[1]
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        if len(mx_records) == 0:
            return False, "Домен почты не существует"
    except:
        return False, "Домен почты не существует"
    
    return True, "OK"

router = APIRouter(prefix="/auth", tags=["auth"])

# Временное хранилище для 2FA сессий (в продакшене использовать Redis)
temp_2fa_sessions = {}


# Pydantic модель для 2FA запроса
class TwoFactorVerifyRequest(BaseModel):
    email: str
    token: str
    temp_token: str


@router.post("/register")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем или email уже существует"
        )
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role or "employee",
        is_active=True,
        registration_status="active"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.post("/login")
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Вход в систему с проверкой 2FA"""
    username = login_data.username or login_data.email
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Требуется username или email"
        )
    
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    # Проверяем статус регистрации
    if user.registration_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Необходимо завершить регистрацию. Перейдите на страницу завершения регистрации."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован. Обратитесь к администратору."
        )
    
    # Проверяем, включена ли 2FA
    if user.is_2fa_enabled:
        # Генерируем временный токен для сессии 2FA
        temp_token = secrets.token_urlsafe(32)
        temp_2fa_sessions[temp_token] = {
            "user_id": user.id,
            "email": user.email,
            "expires": datetime.now() + timedelta(minutes=5)
        }
        
        print(f"Created 2FA session for user {user.email} with temp_token: {temp_token}")
        print(f"Available sessions: {list(temp_2fa_sessions.keys())}")
        
        # Возвращаем JSON с temp_token
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "Требуется код 2FA",
                "temp_token": temp_token,
                "user_id": user.id,
                "email": user.email,
                "requires_2fa": True
            },
            headers={
                "X-Temp-Token": temp_token,
                "X-Requires-2FA": "true"
            }
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

@router.post("/verify-2fa")
async def verify_2fa(
    verify_data: TwoFactorVerifyRequest,
    db: Session = Depends(get_db)
):
    """Проверка 2FA кода при входе"""
    print(f"Received temp_token: '{verify_data.temp_token}'")
    print(f"Available sessions: {list(temp_2fa_sessions.keys())}")
    print(f"All session data: {temp_2fa_sessions}")
    
    # Проверяем временный токен
    if not verify_data.temp_token:
        print("ERROR: temp_token is empty")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="temp_token не передан. Попробуйте войти заново."
        )
    
    if verify_data.temp_token not in temp_2fa_sessions:
        print(f"ERROR: temp_token '{verify_data.temp_token}' not found in sessions")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительная сессия. Попробуйте войти заново."
        )
    
    session = temp_2fa_sessions[verify_data.temp_token]
    
    # Проверяем срок действия
    if session["expires"] < datetime.now():
        del temp_2fa_sessions[verify_data.temp_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла. Попробуйте войти заново."
        )
    
    # Проверяем email
    if session["email"] != verify_data.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email не совпадает"
        )
    
    # Находим пользователя
    user = db.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        del temp_2fa_sessions[verify_data.temp_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    # Проверяем, включена ли 2FA у пользователя
    if not user.is_2fa_enabled or not user.two_factor_secret:
        del temp_2fa_sessions[verify_data.temp_token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA не настроена для этого пользователя"
        )
    
    # Проверяем 2FA код
    try:
        totp = pyotp.TOTP(user.two_factor_secret)
        
        # Проверяем с допуском на 1 шаг времени
        if not totp.verify(verify_data.token, valid_window=1):
            # Проверяем резервные коды
            backup_codes = json.loads(user.backup_codes) if user.backup_codes else []
            if verify_data.token in backup_codes:
                backup_codes.remove(verify_data.token)
                user.backup_codes = json.dumps(backup_codes)
                db.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный код 2FA или резервный код"
                )
    except Exception as e:
        print(f"2FA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка проверки 2FA"
        )
    
    # Удаляем временную сессию
    del temp_2fa_sessions[verify_data.temp_token]
    
    # Создаем токен доступа
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Получить информацию о текущем пользователе"""
    return UserResponse.model_validate(current_user)


@router.get("/registration-status")
async def check_registration_status(
    current_user: User = Depends(get_current_user)
):
    """Проверить статус регистрации текущего пользователя"""
    return {
        "registration_status": current_user.registration_status,
        "is_completed": current_user.registration_status == "active",
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }


@router.post("/logout")
async def logout():
    """Выход из системы"""
    return {"message": "Выход выполнен успешно"}