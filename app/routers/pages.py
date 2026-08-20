from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["pages"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def check_registration_completed(user: User):
    """Проверяет, завершил ли пользователь регистрацию"""
    if user and user.registration_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Необходимо завершить регистрацию",
            headers={"X-Registration-Required": "/pages/complete-registration"}
        )
    return user

async def get_current_user_with_check(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получает текущего пользователя и проверяет статус регистрации"""
    try:
        # Пытаемся получить пользователя через cookie или header
        user = await get_current_user(request, db)
        if user:
            # Проверяем статус регистрации
            if user.registration_status == "pending":
                # Если это API запрос, возвращаем ошибку
                if request.url.path.startswith("/api/"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Необходимо завершить регистрацию"
                    )
                # Если это страница, перенаправляем
                return RedirectResponse(
                    url="/pages/complete-registration",
                    status_code=status.HTTP_302_FOUND
                )
        return user
    except Exception as e:
        # Если пользователь не авторизован, пропускаем (редирект на login будет в другом месте)
        return None

# ==================== ОСНОВНЫЕ СТРАНИЦЫ ====================

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/request-registration", response_class=HTMLResponse)
async def request_registration_page(request: Request):
    """Страница запроса на регистрацию"""
    return templates.TemplateResponse("request_registration.html", {"request": request})

@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """Страница календаря (требует авторизации)"""
    return templates.TemplateResponse("calendar.html", {"request": request})

@router.get("/courses", response_class=HTMLResponse)
async def courses_page(request: Request):
    """Страница курсов (требует авторизации)"""
    return templates.TemplateResponse("courses.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница профиля (требует авторизации)"""
    return templates.TemplateResponse("profile.html", {"request": request})

@router.get("/setting", response_class=HTMLResponse)
async def setting_page(request: Request):
    """Страница настроек (требует авторизации)"""
    return templates.TemplateResponse("setting.html", {"request": request})

@router.get("/login_out", response_class=HTMLResponse)
async def login_out_page(request: Request):
    """Страница выхода"""
    return templates.TemplateResponse("login_out.html", {"request": request})

@router.get("/complete-registration", response_class=HTMLResponse)
async def complete_registration_page(request: Request):
    """Страница завершения регистрации (доступна всем)"""
    return templates.TemplateResponse("complete_registration.html", {"request": request})

# ==================== АДМИН-СТРАНИЦЫ ====================

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Главная админ-страница"""
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/admin/employees", response_class=HTMLResponse)
async def admin_employees(request: Request):
    """Страница управления сотрудниками"""
    return templates.TemplateResponse("admin_employees.html", {"request": request})

@router.get("/admin/courses", response_class=HTMLResponse)
async def admin_courses(request: Request):
    """Страница управления курсами"""
    return templates.TemplateResponse("admin_courses.html", {"request": request})

@router.get("/admin/calendar", response_class=HTMLResponse)
async def admin_calendar(request: Request):
    """Админ-календарь"""
    return templates.TemplateResponse("admin_calendar.html", {"request": request})

@router.get("/admin/profile", response_class=HTMLResponse)
async def admin_profile(request: Request):
    """Профиль администратора"""
    return templates.TemplateResponse("admin_profile.html", {"request": request})

@router.get("/admin/setting", response_class=HTMLResponse)
async def admin_setting(request: Request):
    """Настройки администратора"""
    return templates.TemplateResponse("admin_setting.html", {"request": request})

@router.get("/admin/access", response_class=HTMLResponse)
async def admin_access(request: Request):
    """Управление доступом"""
    return templates.TemplateResponse("admin_access.html", {"request": request})

@router.get("/admin/roles", response_class=HTMLResponse)
async def admin_roles(request: Request):
    """Управление ролями"""
    return templates.TemplateResponse("admin_roles.html", {"request": request})

# ==================== СТРАНИЦА ДЛЯ ТЕСТИРОВАНИЯ ====================

@router.get("/test-registration-check", response_class=HTMLResponse)
async def test_registration_check(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Тестовая страница для проверки статуса регистрации"""
    if user.registration_status == "pending":
        return HTMLResponse("""
        <h1>⚠️ Требуется завершение регистрации</h1>
        <p>Ваш аккаунт еще не активирован.</p>
        <a href="/pages/complete-registration">Завершить регистрацию</a>
        """)
    return HTMLResponse(f"""
    <h1>✅ Регистрация завершена</h1>
    <p>Добро пожаловать, {user.full_name or user.username}!</p>
    <p>Статус: {user.registration_status}</p>
    """)

@router.get("/admin/course-editor/{course_id}", response_class=HTMLResponse)
async def course_editor(request: Request, course_id: int):
    """Страница редактора курса"""
    return templates.TemplateResponse("course_editor.html", {"request": request, "course_id": course_id})


@router.get("/course-view/{course_id}", response_class=HTMLResponse)
async def course_view(request: Request, course_id: int):
    return templates.TemplateResponse("course_view.html", {"request": request, "course_id": course_id})

@router.get("/course-module/{course_id}/{module_id}", response_class=HTMLResponse)
async def course_module(request: Request, course_id: int, module_id: int):
    return templates.TemplateResponse("course_module.html", {"request": request})

@router.get("/admin/stats", response_class=HTMLResponse)
async def admin_stats(request: Request):
    return templates.TemplateResponse("admin_stats.html", {"request": request})

@router.get("/admin/course-stats/{course_id}", response_class=HTMLResponse)
async def admin_course_stats(request: Request, course_id: int):
    return templates.TemplateResponse("admin_course_stats.html", {"request": request, "course_id": course_id})

@router.get("/admin/course-detail/{course_id}", response_class=HTMLResponse)
async def admin_course_detail(request: Request, course_id: int):
    return templates.TemplateResponse("admin_course_detail.html", {"request": request, "course_id": course_id})


@router.get("/admin/user-detail/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(request: Request, user_id: int):
    return templates.TemplateResponse("admin_user_detail.html", {"request": request, "user_id": user_id})