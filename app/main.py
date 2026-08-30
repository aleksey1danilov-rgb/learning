from fastapi import FastAPI, UploadFile, File
from fastapi.responses import RedirectResponse
from app.routers import pages
from app.api.v1 import router as api_router
from app.core.database import engine, Base
from app.core.middleware import RegistrationCheckMiddleware
from fastapi.staticfiles import StaticFiles

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return await call_next(request)

app = FastAPI(
    title="Avito Learning",
    description="Платформа для обучения сотрудников",
    version="1.0.0"
)

app.add_middleware(RegistrationCheckMiddleware)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

Base.metadata.create_all(bind=engine)

# втосоздание админа при первом запуске
from app.core.database import SessionLocal
from app.models.user import User
from app.core.auth import get_password_hash

db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@avito.com',
            full_name='дминистратор системы',
            role='admin',
            hashed_password=get_password_hash('admin123'),
            is_active=True,
            registration_status='completed'
        )
        db.add(admin)
        db.commit()
        print('Admin created automatically')
except Exception as e:
    print(f'Error creating admin: {e}')
finally:
    db.close()

app.include_router(api_router)
app.include_router(pages.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/pages/")



# Эндпоинт для загрузки видео
@app.post("/api/v1/admin/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file"""
    import os
    import uuid
    from fastapi import HTTPException
    
    # Проверяем формат
    allowed_types = ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    # Проверяем размер (30 МБ)
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 100 MB)")
    
    # Сохраняем файл
    uploads_dir = "app/static/uploads/videos"
    os.makedirs(uploads_dir, exist_ok=True)
    
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    filepath = os.path.join(uploads_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(content)
    
    return {"url": f"/static/uploads/videos/{filename}"}


@app.get("/health")
async def health():
    return {"status": "ok", "message": "Сервер работает!"}