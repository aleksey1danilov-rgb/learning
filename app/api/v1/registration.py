from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
import json
import secrets
import pyotp
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.auth import get_current_admin_user, get_current_user, verify_password, get_password_hash, create_access_token
from app.models.user import User, RegistrationRequest, UserRole
from app.schemas.admin import (
    RegistrationRequestCreate, RegistrationRequestResponse,
    RegistrationRequestApprove, RegistrationRequestList,
    TwoFactorSetup, TwoFactorVerify, TwoFactorLogin, BackupCodes,
    RegistrationRequestApproveWithPassword
)

router = APIRouter(prefix="/registration", tags=["registration"])


# ============================================================
# PYDANTIC МОДЕЛИ ДЛЯ ЗАПРОСОВ
# ============================================================

class TemporaryPasswordCheck(BaseModel):
    email: str
    temporary_password: str


class CompleteRegistrationData(BaseModel):
    email: str
    temporary_password: str
    new_password: str
    full_name: Optional[str] = None


# ============================================================
# ПРЕДРЕГИСТРАЦИЯ (для учеников)
# ============================================================

@router.post("/request")
async def create_registration_request(
    request_data: RegistrationRequestCreate,
    db: Session = Depends(get_db)
):
    """Подать заявку на регистрацию (доступно всем)"""
    
    # Проверяем, не зарегистрирован ли уже пользователь
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )
    
    # Проверяем, нет ли уже активной заявки
    existing_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.email == request_data.email,
        RegistrationRequest.status.in_(["pending", "approved"])
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заявка уже подана и ожидает рассмотрения"
        )
    
    # Создаём новую заявку
    new_request = RegistrationRequest(
        email=request_data.email,
        full_name=request_data.full_name,
        description=request_data.description,
        status="pending"
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    return {
        "message": "✅ Заявка успешно подана! Ожидайте подтверждения администратора.",
        "request_id": new_request.id,
        "email": new_request.email,
        "full_name": new_request.full_name,
        "status": new_request.status
    }


# ============================================================
# УПРАВЛЕНИЕ ЗАЯВКАМИ (для админа)
# ============================================================

@router.get("/requests", response_model=RegistrationRequestList)
async def get_all_registration_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить все заявки на регистрацию (только для админа)"""
    
    requests = db.query(RegistrationRequest).all()
    
    pending = [r for r in requests if r.status == "pending"]
    approved = [r for r in requests if r.status == "approved"]
    rejected = [r for r in requests if r.status == "rejected"]
    completed = [r for r in requests if r.status == "completed"]
    
    return RegistrationRequestList(
        pending=pending,
        approved=approved,
        rejected=rejected,
        completed=completed
    )


@router.post("/requests/{request_id}/approve")
async def approve_registration_request(
    request_id: int,
    approve_data: RegistrationRequestApproveWithPassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Одобрить заявку и создать пользователя с временным паролем
    """
    
    reg_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not reg_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    if reg_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Заявка уже {reg_request.status}"
        )
    
    # Проверяем, не существует ли уже пользователь
    existing_user = db.query(User).filter(User.email == reg_request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )
    
    # Генерируем временный пароль (или используем указанный админом)
    temporary_password = approve_data.temporary_password or secrets.token_urlsafe(8)
    hashed_temporary_password = get_password_hash(temporary_password)
    
    # ============================================================
    # СОЗДАЁМ ПОЛЬЗОВАТЕЛЯ СРАЗУ ПРИ ОДОБРЕНИИ
    # ============================================================
    new_user = User(
        username=reg_request.email.split('@')[0],
        email=reg_request.email,
        hashed_password=hashed_temporary_password,
        full_name=reg_request.full_name,
        role=UserRole.EMPLOYEE,
        is_active=True,
        registration_status="pending"  # pending до завершения регистрации
    )
    
    db.add(new_user)
    db.flush()  # Получаем ID пользователя, но не коммитим
    
    # Обновляем заявку
    reg_request.status = "approved"
    reg_request.reviewed_by = current_user.id
    reg_request.reviewed_at = func.now()
    reg_request.temporary_password = hashed_temporary_password
    reg_request.temporary_password_plain = temporary_password
    
    # Сохраняем всё вместе
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "✅ Заявка одобрена! Пользователь создан.",
        "user_id": new_user.id,
        "email": reg_request.email,
        "full_name": reg_request.full_name,
        "temporary_password": temporary_password,
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "registration_status": new_user.registration_status
        }
    }


@router.post("/requests/{request_id}/reject")
async def reject_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Отклонить заявку на регистрацию (только для админа)"""
    
    reg_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not reg_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    if reg_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Заявка уже {reg_request.status}"
        )
    
    reg_request.status = "rejected"
    reg_request.reviewed_by = current_user.id
    reg_request.reviewed_at = func.now()
    
    db.commit()
    
    return {
        "message": "❌ Заявка отклонена.",
        "request_id": request_id,
        "email": reg_request.email
    }


# ============================================================
# ПРОВЕРКА ВРЕМЕННОГО ПАРОЛЯ (исправлено)
# ============================================================

@router.post("/complete-check")
async def check_temporary_password(
    check_data: TemporaryPasswordCheck,
    db: Session = Depends(get_db)
):
    """Проверить временный пароль (для завершения регистрации)"""
    
    reg_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.email == check_data.email,
        RegistrationRequest.status == "approved"
    ).first()
    
    if not reg_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена или не одобрена"
        )
    
    if not verify_password(check_data.temporary_password, reg_request.temporary_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный временный пароль"
        )
    
    return {"valid": True, "user_id": reg_request.id}


# ============================================================
# ЗАВЕРШЕНИЕ РЕГИСТРАЦИИ (исправлено)
# ============================================================

@router.post("/complete")
async def complete_registration(
    complete_data: CompleteRegistrationData,
    db: Session = Depends(get_db)
):
    """Завершить регистрацию: установить постоянный пароль и активировать аккаунт"""
    
    # Находим заявку
    reg_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.email == complete_data.email,
        RegistrationRequest.status == "approved"
    ).first()
    
    if not reg_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена или не одобрена"
        )
    
    # Проверяем временный пароль
    if not verify_password(complete_data.temporary_password, reg_request.temporary_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный временный пароль"
        )
    
    # Находим пользователя
    user = db.query(User).filter(User.email == complete_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Обновляем пароль и статус
    user.hashed_password = get_password_hash(complete_data.new_password)
    user.registration_status = "active"
    if complete_data.full_name:
        user.full_name = complete_data.full_name
    
    # Обновляем заявку
    reg_request.status = "completed"
    reg_request.temporary_password = None
    reg_request.temporary_password_plain = None
    
    db.commit()
    db.refresh(user)
    
    # Создаём токен для автоматического входа
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "message": "✅ Регистрация успешно завершена!",
        "user_id": user.id,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "registration_status": user.registration_status
        }
    }


# ============================================================
# 2FA
# ============================================================

@router.get("/2fa/setup")
async def setup_two_factor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Настройка 2FA"""
    
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA уже включена"
        )
    
    secret = pyotp.random_base32()
    current_user.two_factor_secret = secret
    db.commit()
    
    qr_code = f"otpauth://totp/LearnHub:{current_user.email}?secret={secret}&issuer=LearnHub"
    
    return TwoFactorSetup(
        secret=secret,
        qr_code=qr_code
    )


@router.post("/2fa/verify")
async def verify_two_factor(
    verify_data: TwoFactorVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Подтверждение 2FA"""
    
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA не настроена"
        )
    
    totp = pyotp.TOTP(current_user.two_factor_secret)
    
    if not totp.verify(verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код"
        )
    
    current_user.is_2fa_enabled = True
    
    backup_codes = [secrets.token_hex(4) for _ in range(10)]
    current_user.backup_codes = json.dumps(backup_codes)
    
    db.commit()
    
    return BackupCodes(codes=backup_codes)


@router.post("/2fa/login")
async def login_with_2fa(
    login_data: TwoFactorLogin,
    db: Session = Depends(get_db)
):
    """Вход с 2FA"""
    
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if user.is_2fa_enabled:
        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(login_data.token):
            backup_codes = json.loads(user.backup_codes) if user.backup_codes else []
            if login_data.token in backup_codes:
                backup_codes.remove(login_data.token)
                user.backup_codes = json.dumps(backup_codes)
                db.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный код 2FA"
                )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.post("/2fa/disable")
async def disable_two_factor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отключить 2FA"""
    
    current_user.is_2fa_enabled = False
    current_user.two_factor_secret = None
    current_user.backup_codes = None
    db.commit()
    
    return {"message": "2FA отключена"}


@router.get("/test")
async def test_registration():
    """Тестовый эндпоинт"""
    return {"message": "Registration router works!"}