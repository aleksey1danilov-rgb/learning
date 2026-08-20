from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, Date, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CourseAssignment(Base):
    __tablename__ = "course_assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, expired
    
    # Связи
    course = relationship("Course", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id], back_populates="assigned_courses")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by], back_populates="assigned_by_courses")