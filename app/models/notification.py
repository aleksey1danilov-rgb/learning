from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(50), default="info")  # info, course, meeting, warning
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с событием или курсом
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=True)
    
    read_at = Column(DateTime(timezone=True), nullable=True)
