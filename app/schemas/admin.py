from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Убираем импорт UserRole, используем строки
# from app.models.user import UserRole  # <-- Убираем эту строку

# ============ USER SCHEMAS ============
class UserAdminCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "employee"  # <-- Используем строку вместо UserRole
    is_active: bool = True

class UserAdminUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ COURSE SCHEMAS ============
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    tag: Optional[str] = "primary"
    day: Optional[int] = None
    duration_minutes: Optional[int] = 0
    is_active: Optional[bool] = False
    image_url: Optional[str] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tag: Optional[str] = None
    day: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None 

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    tag: Optional[str]
    day: Optional[int]
    duration_minutes: Optional[int]
    image_url: Optional[str] = None
    is_active: bool
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ PROJECT SCHEMAS ============
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_by: int
    created_at: datetime
    user_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class UserProjectAssign(BaseModel):
    user_id: int
    project_id: int

# ============ COURSE ASSIGNMENT SCHEMAS ============
class CourseAssignmentCreate(BaseModel):
    user_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = "pending"

class CourseAssignmentResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    assigned_by: int
    assigned_at: datetime
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool
    status: str
    course_title: Optional[str] = None
    user_name: Optional[str] = None
    assigned_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# ============ SLIDE SCHEMAS ============
class SlideCreate(BaseModel):
    lesson_id: int
    type: str = "text"
    title: str = ""
    content: str = ""
    timer_seconds: int = 0
    order: int = 0

class SlideUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    timer_seconds: Optional[int] = None

class SlideResponse(BaseModel):
    id: int
    lesson_id: int
    type: str
    title: str
    content: str
    timer_seconds: int
    order: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================
# ДОПОЛНИТЕЛЬНЫЕ СХЕМЫ ДЛЯ РЕДАКТОРА
# ============================================================

class SlideTestData(BaseModel):
    question: str = "Вопрос теста"
    type: str = "single"
    options: List[str] = ["Вариант 1", "Вариант 2"]
    correct: List[int] = [0]

class SlideEditorData(BaseModel):
    id: Optional[int] = None
    title: str = "Новый слайд"
    content: str = "Введите текст..."
    timer_seconds: int = 0
    is_test: bool = False
    test_data: Optional[SlideTestData] = None
    settings: Dict[str, Any] = {
        "font": "Inter",
        "bg_color": "#ffffff",
        "bg_image": "",
        "custom_html": "",
        "lock_until_time": False,
        "lock_time": 10
    }

class LessonEditorData(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    slides: List[SlideEditorData] = []

class ModuleEditorData(BaseModel):
    id: Optional[int] = None
    title: str
    lessons: List[LessonEditorData] = []

class CourseFullData(BaseModel):
    title: str
    description: Optional[str] = None
    tag: Optional[str] = "primary"
    day: Optional[int] = 1
    duration_minutes: Optional[int] = 30
    modules: List[ModuleEditorData] = []

class CourseAssignData(BaseModel):
    user_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class UserSimpleResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    
    class Config:
        from_attributes = True

# ============ PROJECT SCHEMAS ============
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_by: int
    created_at: datetime
    user_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class UserProjectAssign(BaseModel):
    user_id: int
    project_id: int

# ============ USER SCHEMAS ============
class UserAdminCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "employee"
    is_active: bool = True

class UserAdminUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class RegistrationRequestCreate(BaseModel):
    email: str
    full_name: str
    description: Optional[str] = None

class RegistrationRequestResponse(BaseModel):
    id: int
    email: str
    full_name: str
    description: Optional[str]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    
    class Config:
        from_attributes = True

class RegistrationRequestApprove(BaseModel):
    request_id: int
    action: str  # approve или reject

class RegistrationRequestList(BaseModel):
    pending: List[RegistrationRequestResponse]
    approved: List[RegistrationRequestResponse]
    rejected: List[RegistrationRequestResponse]

# ============ 2FA SCHEMAS ============
class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: str  # URL для QR кода

class TwoFactorVerify(BaseModel):
    token: str

class TwoFactorLogin(BaseModel):
    email: str
    password: str
    token: str  # TOTP код

class BackupCodes(BaseModel):
    codes: List[str]

# ============ REGISTRATION SCHEMAS ============
class RegistrationRequestCreate(BaseModel):
    email: str
    full_name: str
    description: Optional[str] = None

class RegistrationRequestApproveWithPassword(BaseModel):
    temporary_password: str = None  # Если не указан, генерируется автоматически
    comment: Optional[str] = None

class RegistrationRequestComplete(BaseModel):
    email: str
    temporary_password: str
    new_password: str
    full_name: Optional[str] = None

# ============ REGISTRATION SCHEMAS ============
class RegistrationRequestCreate(BaseModel):
    email: str
    full_name: str
    description: Optional[str] = None

class RegistrationRequestApproveWithPassword(BaseModel):
    temporary_password: Optional[str] = None
    comment: Optional[str] = None

class RegistrationRequestComplete(BaseModel):
    email: str
    temporary_password: str
    new_password: str
    full_name: Optional[str] = None

class RegistrationRequestResponse(BaseModel):
    id: int
    email: str
    full_name: str
    description: Optional[str]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    
    class Config:
        from_attributes = True

class RegistrationRequestList(BaseModel):
    pending: List[RegistrationRequestResponse]
    approved: List[RegistrationRequestResponse]
    rejected: List[RegistrationRequestResponse]

# ============ 2FA SCHEMAS ============
class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: str

class TwoFactorVerify(BaseModel):
    token: str

class TwoFactorLogin(BaseModel):
    email: str
    password: str
    token: str

class BackupCodes(BaseModel):
    codes: List[str]


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    category: str
    is_default: bool
    
    class Config:
        from_attributes = True

class UserPermissionResponse(BaseModel):
    id: int
    user_id: int
    permission_id: int
    granted_by: Optional[int]
    granted_at: datetime
    is_active: bool
    permission: Optional[PermissionResponse] = None
    
    class Config:
        from_attributes = True

class UserPermissionUpdate(BaseModel):
    permission_id: int
    is_active: bool

class PermissionBulkUpdate(BaseModel):
    user_id: int
    permissions: List[UserPermissionUpdate]
