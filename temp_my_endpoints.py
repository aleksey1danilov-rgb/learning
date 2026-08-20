
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
    for assignment in assignments:
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if course:
            result.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "duration_minutes": course.duration_minutes,
                "tag": course.tag,
                "is_active": course.is_active,
                "image_url": course.image_url,
                "assignment_status": assignment.status,
                "assigned_at": assignment.assigned_at,
                "start_date": assignment.start_date,
                "end_date": assignment.end_date
            })
    
    return result

@router.get("/my/events")
async def get_my_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить события (назначенные курсы) для календаря"""
    assignments = db.query(CourseAssignment).filter(
        CourseAssignment.user_id == current_user.id,
        CourseAssignment.is_active == True
    ).all()
    
    result = []
    for assignment in assignments:
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if course:
            result.append({
                "id": assignment.id,
                "title": course.title,
                "date": str(assignment.assigned_at.date()) if assignment.assigned_at else str(course.created_at.date()),
                "time": str(assignment.assigned_at.time())[:5] if assignment.assigned_at else "09:00",
                "status": assignment.status,
                "course_id": course.id
            })
    
    return result
