from app.models.user import User, UserRole, RegistrationRequest
from app.models.course import Course
from app.models.lesson import Module, Lesson, Slide, Quiz, Question, UserProgress, QuizAttempt
from app.models.course_assignment import CourseAssignment
from app.models.permission import Permission, UserPermission
from app.models.calendar_event import CalendarEvent

__all__ = [
    "User",
    "UserRole",
    "RegistrationRequest",
    "Course",
    "Module",
    "Lesson",
    "Slide",
    "Quiz",
    "Question",
    "UserProgress",
    "QuizAttempt",
    "CourseAssignment",
    "Permission",
    "UserPermission",
    "CalendarEvent"
]
from app.models.notification import Notification

