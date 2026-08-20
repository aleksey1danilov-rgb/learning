from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    TRAINER = "trainer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=True)
    full_name = Column(String(100))
    role = Column(String(20), default=UserRole.EMPLOYEE)
    is_active = Column(Boolean, default=True)
    
    # 2FA
    is_2fa_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(100), nullable=True)
    backup_codes = Column(Text, nullable=True)
    
    # Статус регистрации
    registration_status = Column(String(20), default="pending")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    created_courses = relationship("Course", foreign_keys="Course.created_by", back_populates="creator")
    assigned_courses = relationship("CourseAssignment", foreign_keys="CourseAssignment.user_id", back_populates="user")
    assigned_by_courses = relationship("CourseAssignment", foreign_keys="CourseAssignment.assigned_by", back_populates="assigned_by_user")


class RegistrationRequest(Base):
    __tablename__ = "registration_requests"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, approved, rejected, completed
    
    # Временный пароль для сотрудника
    temporary_password = Column(String(200), nullable=True)  # Хеш временного пароля
    temporary_password_plain = Column(String(50), nullable=True)  # Плоский пароль для отображения
    
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())