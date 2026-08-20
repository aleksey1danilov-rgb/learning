from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    color = Column(String(20), default="#0066ff")
    event_type = Column(String(50), default="meeting")  # meeting, deadline, reminder, holiday
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с пользователем, которому назначено
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    creator = relationship("User", foreign_keys=[created_by], backref="created_calendar_events")
    assignee = relationship("User", foreign_keys=[assigned_to], backref="calendar_events")