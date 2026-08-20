from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from jose import jwt
from app.core.database import SessionLocal
from app.models.user import User
from app.core.config import settings  # <-- ПРАВИЛЬНЫЙ ИМПОРТ


class RegistrationCheckMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Пути, которые всегда доступны (не требуют проверки)
        skip_paths = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/static",
            "/pages/login",
            "/pages/register",
            "/pages/request-registration",
            "/pages/complete-registration",  # Страница завершения регистрации
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/registration/request",
            "/api/v1/registration/complete",
            "/api/v1/registration/complete-check",
            "/api/v1/registration/test",
            "/api/v1/registration/2fa/setup",
            "/api/v1/registration/2fa/verify",
            "/api/v1/registration/2fa/login",
        ]
        
        # Проверяем, нужно ли пропустить запрос
        for path in skip_paths:
            if request.url.path == path or request.url.path.startswith(path + "/"):
                return await call_next(request)
        
        # Проверяем, есть ли токен в заголовках или куках
        token = None
        
        # Проверяем Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        # Если нет токена в заголовках, проверяем куки
        if not token:
            token = request.cookies.get("access_token")
        
        # Если токен есть, проверяем пользователя
        if token:
            try:
                # Декодируем токен
                payload = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=[settings.ALGORITHM]
                )
                user_id = payload.get("sub")
                
                if user_id:
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.id == int(user_id)).first()
                        
                        if user:
                            # Если пользователь не завершил регистрацию
                            if user.registration_status == "pending":
                                # Для API запросов возвращаем ошибку
                                if request.url.path.startswith("/api/"):
                                    raise HTTPException(
                                        status_code=status.HTTP_403_FORBIDDEN,
                                        detail="Необходимо завершить регистрацию",
                                        headers={"X-Registration-Required": "/pages/complete-registration"}
                                    )
                                
                                # Для страниц перенаправляем на завершение регистрации
                                # Но не перенаправляем, если уже на странице завершения
                                if not request.url.path.startswith("/pages/complete-registration"):
                                    return RedirectResponse(
                                        url="/pages/complete-registration",
                                        status_code=status.HTTP_302_FOUND
                                    )
                    finally:
                        db.close()
                        
            except jwt.ExpiredSignatureError:
                # Токен истек - пропускаем, пусть auth обрабатывает
                pass
            except jwt.JWTError:
                # Невалидный токен - пропускаем
                pass
            except Exception as e:
                # Другие ошибки - пропускаем
                print(f"Middleware error: {e}")
                pass
        
        # Продолжаем обработку запроса
        return await call_next(request)