from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime
from app.models.permission import Permission, UserPermission


from app.core.database import get_db
from app.models.course import Course
from app.models.lesson import Module, Lesson, Slide, Quiz, Question,UserProgress
from app.models.user import User
from app.models.course_assignment import CourseAssignment
from app.models.calendar_event import CalendarEvent
from app.models.notification import Notification 
from app.models.user_status import UserStatus
# Проекты временно отключены
# from app.models.project import Project
from app.schemas.admin import (
    CourseResponse, CourseCreate, CourseUpdate,
    CourseFullData,
    CourseAssignData, UserSimpleResponse,
    UserAdminResponse, UserAdminCreate, UserAdminUpdate,
    PermissionResponse, UserPermissionResponse,
    UserPermissionUpdate, PermissionBulkUpdate,
    # ProjectCreate, ProjectUpdate, ProjectResponse, UserProjectAssign  # Временно отключено
)
from app.core.auth import get_current_admin_user, get_current_user


async def get_current_trainer(
    current_user: User = Depends(get_current_user)
):
    """Проверяет что пользователь тренер или админ"""
    if current_user.role not in ['admin', 'trainer']:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user


router = APIRouter(prefix="/admin", tags=["admin"])
print("Admin router created with status-logs endpoint")

# ============================================================
# ТЕСТОВЫЙ ЭНДПОИНТ
# ============================================================

@router.get("/test")
async def test_admin():
    """Тестовый эндпоинт для проверки работы админ-роутера"""
    return {"message": "Admin router works!"}


# ============================================================
# ЭНДПОИНТЫ ДЛЯ КУРСОВ
# ============================================================

@router.get("/courses", response_model=List[CourseResponse])
async def get_all_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Получить все курсы"""
    courses = db.query(Course).all()
    return courses


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Получить курс по ID"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return course


@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    course = Course(
        title=course_data.title,
        description=course_data.description,
        tag=course_data.tag or "primary",
        day=course_data.day,
        duration_minutes=course_data.duration_minutes or 0,
        is_active=course_data.is_active or False,
        created_by=current_user.id,
        image_url=course_data.image_url 
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Удалить курс"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    db.delete(course)
    db.commit()
    return {"message": "Курс удален"}


# ============================================================
# ЭНДПОИНТЫ ДЛЯ ПОЛНОЙ СТРУКТУРЫ КУРСА
# ============================================================

@router.post("/courses/{course_id}/full")
async def save_full_course(
    course_id: int,
    course_data: CourseFullData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Сохранить полную структуру курса (модули, уроки, слайды)"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    # Обновляем основные данные курса
    course.title = course_data.title
    course.description = course_data.description
    course.tag = course_data.tag or "primary"
    course.day = course_data.day or 1
    course.duration_minutes = course_data.duration_minutes or 30
    
    # Удаляем старые модули и все связанные данные
    old_modules = db.query(Module).filter(Module.course_id == course_id).all()
    for old_module in old_modules:
        old_lessons = db.query(Lesson).filter(Lesson.module_id == old_module.id).all()
        for old_lesson in old_lessons:
            # Удаляем вопросы тестов
            old_quizzes = db.query(Quiz).filter(Quiz.lesson_id == old_lesson.id).all()
            for old_quiz in old_quizzes:
                db.query(Question).filter(Question.quiz_id == old_quiz.id).delete()
                db.delete(old_quiz)
            # Удаляем слайды
            db.query(Slide).filter(Slide.lesson_id == old_lesson.id).delete()
            # Удаляем урок
            db.delete(old_lesson)
        # Удаляем модуль
        db.delete(old_module)
    
    # Важно: коммитим удаление до создания новых
    db.flush()
    
    # Создаём новые модули
    for module_idx, module_data in enumerate(course_data.modules):
        module = Module(
            course_id=course_id,
            title=module_data.title,
            order=module_idx,
            is_published=True
        )
        db.add(module)
        db.flush()
        
        # Создаём уроки в модуле
        for lesson_idx, lesson_data in enumerate(module_data.lessons):
            lesson = Lesson(
                module_id=module.id,
                title=lesson_data.title,
                description=lesson_data.description or "",
                order=lesson_idx,
                is_required=True
            )
            db.add(lesson)
            db.flush()
            
            # Создаём слайды в уроке
            for slide_idx, slide_data in enumerate(lesson_data.slides):
                # Сохраняем настройки в content как JSON
                slide_settings = slide_data.settings if slide_data.settings else {}
                content_json = json.dumps({
                    "content": slide_data.content or "",
                    "settings": slide_settings
                })
                
                slide = Slide(
                    lesson_id=lesson.id,
                    type="test" if slide_data.is_test else "text",
                    title=slide_data.title or "Слайд " + str(slide_idx + 1),
                    content=content_json,
                    timer_seconds=slide_data.timer_seconds or 0,
                    order=slide_idx
                )
                db.add(slide)
                db.flush()
                
                # Если есть тест, создаём викторину
                if slide_data.is_test and slide_data.test_data:
                    quiz = Quiz(
                        lesson_id=lesson.id,
                        title="Тест: " + (slide_data.title or ""),
                        passing_score=70
                    )
                    db.add(quiz)
                    db.flush()
                    
                    # Создаём вопрос
                    test_data = slide_data.test_data
                    question = Question(
                        quiz_id=quiz.id,
                        text=test_data.get("question", "Вопрос теста"),
                        type=test_data.get("type", "single"),
                        options=json.dumps(test_data.get("options", ["Вариант 1", "Вариант 2"])),
                        correct_answer=json.dumps(test_data.get("correct", [0])),
                        order=0
                    )
                    db.add(question)
    
    db.commit()
    return {"message": "Курс успешно сохранен", "course_id": course_id}

@router.get("/courses/{course_id}/full")
async def get_full_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Получить полную структуру курса для редактора"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    # Загружаем все связанные данные
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    
    result_modules = []
    for module in modules:
        module_data = {
            "id": module.id,
            "title": module.title,
            "lessons": []
        }
        
        lessons = db.query(Lesson).filter(Lesson.module_id == module.id).order_by(Lesson.order).all()
        for lesson in lessons:
            lesson_data = {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "slides": []
            }
            
            slides = db.query(Slide).filter(Slide.lesson_id == lesson.id).order_by(Slide.order).all()
            for slide in slides:
                # Пытаемся распарсить JSON из content
                try:
                    content_data = json.loads(slide.content) if slide.content else {}
                    slide_content = content_data.get("content", slide.content)
                    slide_settings = content_data.get("settings", {})
                except:
                    slide_content = slide.content or ""
                    slide_settings = {
                        "font": "Inter",
                        "bg_color": "#ffffff",
                        "bg_image": "",
                        "lock_until_time": False,
                        "lock_time": 10
                    }
                
                slide_data = {
                    "id": slide.id,
                    "title": slide.title,
                    "content": slide_content,
                    "timer_seconds": slide.timer_seconds,
                    "is_test": slide.type == "test",
                    "test_data": None,
                    "settings": slide_settings
                }
                
                # Если есть тест, загружаем данные
                if slide.type == "test":
                    quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson.id).first()
                    if quiz:
                        questions = db.query(Question).filter(Question.quiz_id == quiz.id).order_by(Question.order).all()
                        if questions:
                            q = questions[0]
                            try:
                                options = json.loads(q.options) if isinstance(q.options, str) else q.options
                                correct = json.loads(q.correct_answer) if isinstance(q.correct_answer, str) else q.correct_answer
                            except:
                                options = ["Вариант 1", "Вариант 2"]
                                correct = [0]
                            
                            slide_data["test_data"] = {
                                "question": q.text,
                                "type": q.type,
                                "options": options,
                                "correct": correct
                            }
                
                lesson_data["slides"].append(slide_data)
            
            module_data["lessons"].append(lesson_data)
        
        result_modules.append(module_data)
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "image_url": course.image_url,
        "tag": course.tag,
        "day": course.day,
        "duration_minutes": course.duration_minutes,
        "is_active": course.is_active,
        "created_by": course.created_by,
        "created_at": course.created_at,
        "modules": result_modules
    }

# ============================================================
# ЭНДПОИНТЫ ДЛЯ НАЗНАЧЕНИЯ КУРСОВ
# ============================================================

@router.post("/courses/{course_id}/assign")
async def assign_course(
    course_id: int,
    assignment_data: CourseAssignData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Назначить курс пользователю"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    user = db.query(User).filter(User.id == assignment_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    existing = db.query(CourseAssignment).filter(
        CourseAssignment.course_id == course_id,
        CourseAssignment.user_id == assignment_data.user_id,
        CourseAssignment.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Курс уже назначен этому пользователю")
    
    # Получаем все слайды курса
    slides = db.query(Slide).join(Lesson).join(Module).filter(Module.course_id == course_id).all()
    slide_ids = [s.id for s in slides]
    
    # Удаляем старый прогресс по этому курсу
    if slide_ids:
        db.query(UserProgress).filter(
            UserProgress.user_id == assignment_data.user_id,
            UserProgress.slide_id.in_(slide_ids)
        ).delete()
    
    assignment = CourseAssignment(
        course_id=course_id,
        user_id=assignment_data.user_id,
        assigned_by=current_user.id,
        start_date=assignment_data.start_date,
        end_date=assignment_data.end_date,
        status="pending"
    )
    db.add(assignment)
    
    # Создаём уведомление
    notification = Notification(
        user_id=assignment_data.user_id,
        title="📚 Назначен новый курс",
        message=f"Вам назначен курс: {course.title}",
        type="course",
        course_id=course_id
    )
    db.add(notification)
    
    db.commit()
    db.refresh(assignment)
    return {"message": "Курс назначен", "assignment_id": assignment.id}

@router.get("/courses/users", response_model=List[UserSimpleResponse])
async def get_all_users_for_assign(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить всех пользователей для назначения курсов"""
    users = db.query(User).filter(User.role != "admin").all()
    return users


@router.get("/courses/{course_id}/assignments")
async def get_course_assignments(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить все назначения курса"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    assignments = db.query(CourseAssignment).filter(
        CourseAssignment.course_id == course_id
    ).all()
    
    result = []
    for ass in assignments:
        user = db.query(User).filter(User.id == ass.user_id).first()
        assigner = db.query(User).filter(User.id == ass.assigned_by).first()
        result.append({
            "id": ass.id,
            "user_id": ass.user_id,
            "user_name": user.full_name if user else "Неизвестно",
            "assigned_by": ass.assigned_by,
            "assigned_by_name": assigner.full_name if assigner else "Неизвестно",
            "assigned_at": ass.assigned_at,
            "start_date": ass.start_date,
            "end_date": ass.end_date,
            "status": ass.status,
            "is_active": ass.is_active
        })
    
    return result


# ============================================================
# ЭНДПОИНТЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ (СОТРУДНИКОВ)
# ============================================================

@router.get("/users", response_model=List[UserAdminResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить всех пользователей"""
    users = db.query(User).all()
    return users


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить пользователя по ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("/users", response_model=UserAdminResponse)
async def create_user(
    user_data: UserAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать нового пользователя"""
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем или email уже существует"
        )
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=user_data.is_active
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Не даем изменить роль администратора
    if user.role == "admin" and user.id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Нельзя изменять другого администратора"
        )
    
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Не даем удалить самого себя
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить самого себя"
        )
    
    # Не даем удалить другого администратора
    if user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Нельзя удалить другого администратора"
        )
    
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удален", "user_id": user_id}


# ============================================================
# ЭНДПОИНТЫ ДЛЯ НАЗНАЧЕНИЙ КУРСОВ (ДОПОЛНИТЕЛЬНЫЕ)
# ============================================================

@router.get("/assignments")
async def get_all_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить все назначения курсов"""
    assignments = db.query(CourseAssignment).all()
    
    result = []
    for ass in assignments:
        course = db.query(Course).filter(Course.id == ass.course_id).first()
        user = db.query(User).filter(User.id == ass.user_id).first()
        assigner = db.query(User).filter(User.id == ass.assigned_by).first()
        
        result.append({
            "id": ass.id,
            "course_id": ass.course_id,
            "course_title": course.title if course else "Неизвестно",
            "user_id": ass.user_id,
            "user_name": user.full_name if user else "Неизвестно",
            "assigned_by": ass.assigned_by,
            "assigned_by_name": assigner.full_name if assigner else "Неизвестно",
            "assigned_at": ass.assigned_at,
            "start_date": ass.start_date,
            "end_date": ass.end_date,
            "status": ass.status,
            "is_active": ass.is_active
        })
    
    return result


# ============================================================
# ЭНДПОИНТЫ ДЛЯ РЕГИСТРАЦИОННЫХ ЗАЯВОК
# ============================================================

@router.get("/registration-requests")
async def get_registration_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить все заявки на регистрацию"""
    from app.models.user import RegistrationRequest
    
    requests = db.query(RegistrationRequest).all()
    
    result = {
        "pending": [],
        "approved": [],
        "rejected": [],
        "completed": []
    }
    
    for req in requests:
        item = {
            "id": req.id,
            "email": req.email,
            "full_name": req.full_name,
            "description": req.description,
            "status": req.status,
            "created_at": req.created_at,
            "reviewed_at": req.reviewed_at,
            "reviewed_by": req.reviewed_by
        }
        if req.status == "pending":
            result["pending"].append(item)
        elif req.status == "approved":
            result["approved"].append(item)
        elif req.status == "rejected":
            result["rejected"].append(item)
    
    return result


@router.post("/registration-requests/{request_id}/approve")
async def approve_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Одобрить заявку на регистрацию"""
    from app.models.user import RegistrationRequest
    
    reg_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not reg_request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if reg_request.status != "pending":
        raise HTTPException(status_code=400, detail=f"Заявка уже {reg_request.status}")
    
    reg_request.status = "approved"
    reg_request.reviewed_by = current_user.id
    reg_request.reviewed_at = datetime.now()
    
    db.commit()
    
    return {"message": "Заявка одобрена"}


@router.post("/registration-requests/{request_id}/reject")
async def reject_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Отклонить заявку на регистрацию"""
    from app.models.user import RegistrationRequest
    
    reg_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not reg_request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if reg_request.status != "pending":
        raise HTTPException(status_code=400, detail=f"Заявка уже {reg_request.status}")
    
    reg_request.status = "rejected"
    reg_request.reviewed_by = current_user.id
    reg_request.reviewed_at = datetime.now()
    
    db.commit()
    
    return {"message": "Заявка отклонена"}

@router.get("/permissions", response_model=List[PermissionResponse])
async def get_all_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить все права доступа"""
    return db.query(Permission).all()

@router.get("/users/{user_id}/permissions", response_model=List[UserPermissionResponse])
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить права конкретного пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    permissions = db.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.is_active == True
    ).all()
    
    return permissions

@router.post("/users/{user_id}/permissions/bulk")
async def update_user_permissions_bulk(
    user_id: int,
    data: PermissionBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Массовое обновление прав пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Удаляем старые права
    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    
    # Создаём новые
    for perm_data in data.permissions:
        if perm_data.is_active:
            up = UserPermission(
                user_id=user_id,
                permission_id=perm_data.permission_id,
                granted_by=current_user.id
            )
            db.add(up)
    
    db.commit()
    return {"message": "Права обновлены", "user_id": user_id}

@router.post("/users/{user_id}/permissions/request")
async def request_permission(
    user_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Запросить право (для админа — сразу выдать)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Право не найдено")
    
    existing = db.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.permission_id == permission_id,
        UserPermission.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Право уже выдано")
    
    up = UserPermission(
        user_id=user_id,
        permission_id=permission_id,
        granted_by=current_user.id
    )
    db.add(up)
    db.commit()
    db.refresh(up)
    
    return {"message": "Право выдано", "permission": permission.code}

# ============================================================
# ЭНДПОИНТЫ ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

from app.core.auth import get_current_user

@router.get("/my/courses")
async def get_my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить курсы, назначенные текущему пользователю"""
    assignments = db.query(CourseAssignment).filter(
        CourseAssignment.user_id == current_user.id
    ).all()
    result = []
    for a in assignments:
        course = db.query(Course).filter(Course.id == a.course_id).first()
        if course:
            result.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "duration_minutes": course.duration_minutes,
                "tag": course.tag,
                "is_active": course.is_active,
                "image_url": course.image_url,
                "assignment_status": a.status,
                "assigned_at": str(a.assigned_at) if a.assigned_at else None,
                "start_date": str(a.start_date) if a.start_date else None,
                "end_date": str(a.end_date) if a.end_date else None
            })
    return result


@router.get("/my/events")
async def get_my_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить события для календаря текущего пользователя"""
    assignments = db.query(CourseAssignment).filter(
        CourseAssignment.user_id == current_user.id,
        CourseAssignment.is_active == True
    ).all()
    result = []
    for a in assignments:
        course = db.query(Course).filter(Course.id == a.course_id).first()
        if course:
            result.append({
                "id": a.id,
                "title": course.title,
                "date": str(a.assigned_at.date()) if a.assigned_at else str(course.created_at.date()),
                "time": str(a.assigned_at.time())[:5] if a.assigned_at else "09:00",
                "status": a.status,
                "course_id": course.id
            })
    return result


@router.get("/my/courses/{course_id}/full")
async def get_my_course_full(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить структуру курса для обучения"""
    assignment = db.query(CourseAssignment).filter(
        CourseAssignment.course_id == course_id,
        CourseAssignment.user_id == current_user.id
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Курс не назначен вам")
    
    # Используем существующую функцию get_full_course
    return await get_full_course(course_id, db, current_user)


@router.get("/my/courses/{course_id}/modules/{module_id}")
async def get_my_module(
    course_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить модуль с уроками и слайдами для обучения"""
    assignment = db.query(CourseAssignment).filter(
        CourseAssignment.course_id == course_id,
        CourseAssignment.user_id == current_user.id
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Курс не назначен")
    
    module = db.query(Module).filter(Module.id == module_id, Module.course_id == course_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Модуль не найден")
    
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.order).all()
    
    result = {
        "id": module.id,
        "title": module.title,
        "course_id": course_id,
        "lessons": []
    }
    
    for lesson in lessons:
        slides = db.query(Slide).filter(Slide.lesson_id == lesson.id).order_by(Slide.order).all()
        lesson_data = {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "slides": []
        }
        for slide in slides:
            # Парсим settings из JSON если есть
            try:
                settings = json.loads(slide.settings) if isinstance(slide.settings, str) else slide.settings
            except:
                settings = {}
            
            slide_data = {
                "id": slide.id,
                "title": slide.title,
                "type": slide.type,
                "content": slide.content,
                "timer_seconds": slide.timer_seconds,
                "settings": settings,
                "order": slide.order
            }
            if slide.type == "test":
                quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson.id).first()
                if quiz:
                    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
                    if questions:
                        q = questions[0]
                        try:
                            options = json.loads(q.options) if isinstance(q.options, str) else q.options
                            correct = json.loads(q.correct_answer) if isinstance(q.correct_answer, str) else q.correct_answer
                        except:
                            options = ["Вариант 1", "Вариант 2"]
                            correct = [0]
                        slide_data["test_data"] = {
                            "question": q.text,
                            "type": q.type,
                            "options": options,
                            "correct": correct
                        }
            lesson_data["slides"].append(slide_data)
        result["lessons"].append(lesson_data)
    
    return result


@router.get("/my/progress")
async def get_my_progress(
    course_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить прогресс пользователя"""
    from app.models.lesson import UserProgress
    
    query = db.query(UserProgress).filter(UserProgress.user_id == current_user.id)
    
    if course_id:
        slides = db.query(Slide).join(Lesson).join(Module).filter(Module.course_id == course_id).all()
        slide_ids = [s.id for s in slides]
        query = query.filter(UserProgress.slide_id.in_(slide_ids))
    
    results = query.all()
    return [{
        "slide_id": r.slide_id,
        "is_completed": r.is_completed,
        "completed_at": str(r.completed_at) if r.completed_at else None,
        "time_spent": r.time_spent if r.time_spent else 0
    } for r in results]

@router.post("/my/progress")
async def save_my_progress(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Сохранить прогресс прохождения слайда"""
    slide_id = data.get('slide_id')
    
    if not slide_id:
        raise HTTPException(status_code=400, detail="slide_id обязателен")
    
    existing = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.slide_id == slide_id
    ).first()
    
    if existing:
        existing.is_completed = True
        existing.completed_at = datetime.now()
    else:
        progress = UserProgress(
            user_id=current_user.id,
            slide_id=slide_id,
            is_completed=True,
            completed_at=datetime.now()
        )
        db.add(progress)
    
    # Находим курс по slide_id и обновляем статус назначения
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if slide:
        lesson = db.query(Lesson).filter(Lesson.id == slide.lesson_id).first()
        if lesson:
            module = db.query(Module).filter(Module.id == lesson.module_id).first()
            if module:
                assignment = db.query(CourseAssignment).filter(
                    CourseAssignment.user_id == current_user.id,
                    CourseAssignment.course_id == module.course_id
                ).first()
                if assignment:
                    # Проверяем все ли слайды курса пройдены
                    all_slides = db.query(Slide).join(Lesson).join(Module).filter(
                        Module.course_id == module.course_id
                    ).all()
                    all_slide_ids = [s.id for s in all_slides]
                    
                    completed = db.query(UserProgress).filter(
                        UserProgress.user_id == current_user.id,
                        UserProgress.slide_id.in_(all_slide_ids),
                        UserProgress.is_completed == True
                    ).count()
                    
                    if completed >= len(all_slide_ids):
                        assignment.status = "completed"
                    elif completed > 0:
                        assignment.status = "in_progress"
                    else:
                        assignment.status = "pending"
    
    db.commit()
    return {"message": "Прогресс сохранён", "slide_id": slide_id}

@router.post("/calendar-events")
async def create_calendar_event(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Создать событие календаря"""
    event = CalendarEvent(
        title=data.get('title'),
        description=data.get('description', ''),
        start_time=datetime.fromisoformat(data.get('start_time')),
        end_time=datetime.fromisoformat(data.get('end_time')),
        color=data.get('color', '#0066ff'),
        event_type=data.get('event_type', 'meeting'),
        created_by=current_user.id,
        assigned_to=data.get('assigned_to')
    )
    db.add(event)
    
    # Уведомление для назначенного сотрудника
    if data.get('assigned_to'):
        notification = Notification(
            user_id=data['assigned_to'],
            title="📅 Новая встреча",
            message=data.get('title', ''),
            type="meeting",
            event_id=event.id
        )
        db.add(notification)
    
    db.commit()
    db.refresh(event)
    return event

@router.get("/my/calendar-events")
async def get_my_calendar_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить события календаря для пользователя"""
    events = db.query(CalendarEvent).filter(
        (CalendarEvent.assigned_to == current_user.id) | (CalendarEvent.assigned_to == None)
    ).all()
    return [{
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "start_time": str(e.start_time),
        "end_time": str(e.end_time),
        "color": e.color,
        "event_type": e.event_type,
        "date": str(e.start_time.date()),
        "time": str(e.start_time.time())[:5]
    } for e in events]

@router.get("/calendar-events")
async def get_calendar_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Получить все события календаря"""
    events = db.query(CalendarEvent).all()
    return [{
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "start_time": str(e.start_time),
        "end_time": str(e.end_time),
        "color": e.color,
        "event_type": e.event_type,
        "assigned_to": e.assigned_to,
        "date": str(e.start_time.date()),
        "time": str(e.start_time.time())[:5]
    } for e in events]

@router.get("/my/notifications")
async def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить уведомления пользователя"""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    return [{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "is_read": n.is_read,
        "created_at": str(n.created_at),
        "course_id": n.course_id,
        "event_id": n.event_id
    } for n in notifications]


@router.post("/my/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отметить уведомление как прочитанное"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if notification:
        notification.is_read = True
        notification.read_at = datetime.now()
        db.commit()
    
    return {"message": "ok"}


@router.post("/my/notifications/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отметить все уведомления как прочитанные"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True, "read_at": datetime.now()})
    db.commit()
    return {"message": "ok"}

router.get("/my/status")
async def get_my_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить текущий статус пользователя"""
    status = db.query(UserStatus).filter(
        UserStatus.user_id == current_user.id
    ).order_by(UserStatus.created_at.desc()).first()
    
    if not status:
        # По умолчанию — обучаюсь
        status = UserStatus(user_id=current_user.id, status="learning")
        db.add(status)
        db.commit()
        db.refresh(status)
    
    return {"id": status.id, "user_id": status.user_id, "status": status.status, "created_at": str(status.created_at)}


@router.post("/my/status")
async def update_my_status(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user status with timer"""
    new_status = data.get('status', 'learning')
    previous_status = data.get('previous_status', None)
    
    # Deactivate all previous active statuses
    db.query(UserStatus).filter(
        UserStatus.user_id == current_user.id,
        UserStatus.is_active == True
    ).update({
        "is_active": False,
        "ended_at": datetime.now()
    })
    
    # Create new status
    status = UserStatus(
        user_id=current_user.id,
        status=new_status,
        previous_status=previous_status,
        started_at=datetime.now(),
        is_active=True
    )
    db.add(status)
    db.commit()
    db.refresh(status)
    
    return {
        "message": "Status updated", 
        "status": status.status,
        "id": status.id,
        "started_at": str(status.started_at)
    }

@router.post("/my/status/heartbeat")
async def status_heartbeat(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update status duration (heartbeat)"""
    from datetime import datetime as dt
    
    status = db.query(UserStatus).filter(
        UserStatus.user_id == current_user.id,
        UserStatus.is_active == True
    ).order_by(UserStatus.created_at.desc()).first()
    
    if status:
        status.duration_seconds = data.get('duration_seconds', 0)
        # Обновляем время последнего heartbeat
        status.started_at = dt.now()  # или добавить поле last_heartbeat
        db.commit()
        return {"message": "Heartbeat received", "duration": status.duration_seconds}
    
    return {"message": "No active status found"}


@router.get("/check-offline-statuses")
async def check_offline_statuses():
    """Проверяет статусы и ставит offline если нет heartbeat более 2 минут"""
    from datetime import datetime as dt, timedelta
    
    db = SessionLocal()
    try:
        active_statuses = db.query(UserStatus).filter(
            UserStatus.is_active == True,
            UserStatus.status != 'offline'
        ).all()
        
        now = dt.now()
        for status in active_statuses:
            if status.started_at:
                started = status.started_at
                if started.tzinfo:
                    started = started.replace(tzinfo=None)
                # Если heartbeat не было более 2 минут - ставим offline
                if now - started > timedelta(minutes=2):
                    status.is_active = False
                    status.ended_at = now
                    # Создаем новый статус offline
                    new_status = UserStatus(
                        user_id=status.user_id,
                        status='offline',
                        previous_status=status.status,
                        started_at=now,
                        is_active=True
                    )
                    db.add(new_status)
        
        db.commit()
        return {"message": "Offline check completed"}
    finally:
        db.close()




@router.get("/users/{user_id}/statuses")
async def get_user_statuses(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить историю статусов пользователя (для админа)"""
    statuses = db.query(UserStatus).filter(
        UserStatus.user_id == user_id
    ).order_by(UserStatus.created_at.desc()).limit(20).all()
    
    return [{
        "id": s.id,
        "user_id": s.user_id,
        "status": s.status,
        "created_at": str(s.created_at)
    } for s in statuses]


@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...), current_user: User = Depends(get_current_admin_user)):
    """Upload video file"""
    import os
    import uuid
    
    allowed_types = ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    content_data = await file.read()
    if len(content_data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50 MB)")
    
    uploads_dir = "app/static/uploads/videos"
    os.makedirs(uploads_dir, exist_ok=True)
    
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    filepath = os.path.join(uploads_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(content_data)
    
    return {"url": f"/static/uploads/videos/{filename}"}


@router.get("/status-logs")
async def get_status_logs(
    user_id: int = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all status transition logs for admin with filters"""
    query = db.query(UserStatus)
    
    if user_id:
        query = query.filter(UserStatus.user_id == user_id)
    
    if date_from:
        from datetime import datetime as dt
        date_from_dt = dt.strptime(date_from, '%Y-%m-%d')
        query = query.filter(UserStatus.started_at >= date_from_dt)
    
    if date_to:
        from datetime import datetime as dt
        date_to_dt = dt.strptime(date_to, '%Y-%m-%d')
        date_to_dt = date_to_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(UserStatus.started_at <= date_to_dt)
    
    statuses = query.order_by(UserStatus.started_at.desc()).limit(200).all()
    
    result = []
    for s in statuses:
        user = db.query(User).filter(User.id == s.user_id).first()
        result.append({
            "id": s.id,
            "user_id": s.user_id,
            "user_name": user.full_name if user else "Unknown",
            "user_email": user.email if user else "",
            "status": s.status,
            "previous_status": s.previous_status,
            "started_at": str(s.started_at) if s.started_at else None,
            "ended_at": str(s.ended_at) if s.ended_at else None,
            "duration_seconds": s.duration_seconds,
            "is_active": s.is_active
        })
    
    return result
@router.get("/roles")
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all roles with permissions"""
    roles = db.query(Permission).all() if hasattr(Permission, '__tablename__') else []
    
    # Возвращаем стандартные роли
    return [
        {
            "id": 1,
            "name": "employee",
            "label": "Сотрудник",
            "description": "Базовый доступ: просмотр курсов, календаря, прохождение обучения",
            "permissions": ["view_courses", "view_calendar", "complete_lessons"]
        },
        {
            "id": 2,
            "name": "trainer",
            "label": "Тренер",
            "description": "Создание курсов, редактирование, создание событий в календаре",
            "permissions": ["view_courses", "view_calendar", "complete_lessons", "create_courses", "edit_courses", "create_events", "edit_events"]
        },
        {
            "id": 3,
            "name": "admin",
            "label": "Администратор",
            "description": "Полный доступ ко всем разделам",
            "permissions": ["view_courses", "view_calendar", "complete_lessons", "create_courses", "edit_courses", "create_events", "edit_events", "manage_users", "manage_roles", "view_statistics"]
        }
    ]

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update user role"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    new_role = data.get('role')
    if new_role not in ['employee', 'trainer', 'admin']:
        raise HTTPException(status_code=400, detail="Неверная роль")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя изменить свою роль")
    
    user.role = new_role
    db.commit()
    
    return {"message": f"Роль пользователя {user.full_name or user.username} изменена на {new_role}"}
