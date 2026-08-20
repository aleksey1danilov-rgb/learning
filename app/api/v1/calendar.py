from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.course_assignment import CourseAssignment
from app.core.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])

@router.get("/my")
async def get_my_calendar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить события календаря для текущего пользователя"""
    assignments = db.query(CourseAssignment).filter(
        CourseAssignment.user_id == current_user.id,
        CourseAssignment.is_active == True
    ).all()
    
    events = []
    for assignment in assignments:
        if assignment.start_date:
            events.append({
                "id": assignment.id,
                "title": assignment.course.title,
                "date": assignment.start_date.isoformat(),
                "type": "course",
                "status": assignment.status,
                "course_id": assignment.course_id
            })
    
    return events