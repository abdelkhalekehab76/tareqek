"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ─── Enums mirrored for API ───
class UserRoleEnum(str, Enum):
    ADMIN = "ADMIN"
    STUDENT = "STUDENT"


class AccountStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# ─── Auth ───
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=4, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    must_change_password: bool = False
    user_id: int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ─── User / Student ───
class UserBase(BaseModel):
    username: str
    full_name: str
    phone: Optional[str] = None
    role: UserRoleEnum = UserRoleEnum.STUDENT
    status: AccountStatusEnum = AccountStatusEnum.ACTIVE


class StudentCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=4, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    teacher_name: Optional[str] = None
    group_name: Optional[str] = None
    current_juz: int = 1
    current_surah: int = 1
    notes: Optional[str] = None


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    teacher_name: Optional[str] = None
    group_name: Optional[str] = None
    current_juz: Optional[int] = None
    current_surah: Optional[int] = None
    current_ayah: Optional[int] = None
    memorization_status: Optional[str] = None
    revision_status: Optional[str] = None
    notes: Optional[str] = None
    notes_visible_to_student: Optional[bool] = None
    status: Optional[AccountStatusEnum] = None
    city: Optional[str] = None
    country: Optional[str] = None


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=4, max_length=128)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    full_name: str
    phone: Optional[str] = None
    status: str
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    enrollment_date: Optional[date] = None
    current_juz: int
    current_surah: int
    current_ayah: int
    memorization_status: Optional[str] = None
    revision_status: Optional[str] = None
    teacher_name: Optional[str] = None
    group_name: Optional[str] = None
    notes: Optional[str] = None
    notes_visible_to_student: bool = False
    total_pages_memorized: float = 0
    total_pages_revised: float = 0
    average_grade: Optional[float] = None
    completed_juz_count: int = 0
    city: Optional[str] = None
    country: Optional[str] = None
    created_at: Optional[datetime] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    status: str
    phone: Optional[str] = None
    must_change_password: bool
    last_login: Optional[datetime] = None


# ─── Progress ───
class ProgressCreate(BaseModel):
    student_id: int
    juz: int = Field(..., ge=1, le=30)
    surah: int = Field(..., ge=1, le=114)
    from_ayah: int = Field(..., ge=1)
    to_ayah: int = Field(..., ge=1)
    pages_amount: float = 0.0
    status: str = "COMPLETED"
    is_revision: bool = False
    record_date: Optional[date] = None
    notes: Optional[str] = None


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    juz: int
    surah: int
    from_ayah: int
    to_ayah: int
    pages_amount: float
    status: str
    is_revision: bool
    record_date: date
    notes: Optional[str] = None
    created_at: datetime


# ─── Exam ───
class ExamCreate(BaseModel):
    student_id: int
    title: str
    exam_type: str = "GENERAL"
    exam_date: date
    juz: Optional[int] = None
    surah: Optional[int] = None
    from_ayah: Optional[int] = None
    to_ayah: Optional[int] = None
    grade: float
    max_grade: float = 100.0
    teacher_notes: Optional[str] = None
    general_notes: Optional[str] = None


class ExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    title: str
    exam_type: str
    exam_date: date
    juz: Optional[int] = None
    surah: Optional[int] = None
    from_ayah: Optional[int] = None
    to_ayah: Optional[int] = None
    grade: float
    max_grade: float
    percentage: Optional[float] = None
    teacher_notes: Optional[str] = None
    general_notes: Optional[str] = None
    created_at: datetime


# ─── Schedule / Event / Announcement ───
class ScheduleCreate(BaseModel):
    student_id: Optional[int] = None
    group_name: Optional[str] = None
    title: str
    schedule_type: str = "class"
    schedule_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    teacher_name: Optional[str] = None
    notes: Optional[str] = None


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: Optional[int] = None
    group_name: Optional[str] = None
    title: str
    schedule_type: str
    schedule_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    teacher_name: Optional[str] = None
    notes: Optional[str] = None


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    is_visible: bool = True


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    event_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    is_visible: bool


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    is_important: bool = False
    is_published: bool = True


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    is_important: bool
    is_published: bool
    publish_at: datetime
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: Optional[int] = None  # null = all students
    user_ids: Optional[List[int]] = None
    title: str
    message: str
    link: Optional[str] = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime


# ─── Plan / Goal / Tasbeeh ───
class PlanCreate(BaseModel):
    title: str
    start_date: date
    target_date: Optional[date] = None
    frequency_days: int = 1
    memorize_pages: float = 1.0
    revision_pages: float = 2.0


class GoalCreate(BaseModel):
    title: str
    target_value: float
    unit: str = "صفحة"
    deadline: Optional[date] = None


class TasbeehUpdate(BaseModel):
    count: int
    target: int = 33
    dhikr_text: str = "سبحان الله"
