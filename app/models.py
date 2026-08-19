"""
SQLAlchemy models - normalized relational schema.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, Date,
    ForeignKey, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STUDENT = "STUDENT"


class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class ExamType(str, enum.Enum):
    NEW_MEMORIZATION = "NEW_MEMORIZATION"
    REVISION = "REVISION"
    RECITATION = "RECITATION"
    TAJWEED = "TAJWEED"
    GENERAL = "GENERAL"
    MONTHLY = "MONTHLY"
    FINAL = "FINAL"


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ProgressStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REVISION = "REVISION"


class GoalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ───────────────────────────── Users ─────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    status = Column(SAEnum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(30), nullable=True)
    must_change_password = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    parent_name = Column(String(200), nullable=True)
    parent_phone = Column(String(30), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    enrollment_date = Column(Date, default=date.today)
    current_juz = Column(Integer, default=1)
    current_surah = Column(Integer, default=1)  # 1-114
    current_ayah = Column(Integer, default=1)
    memorization_status = Column(String(50), default="جديد")
    revision_status = Column(String(50), default="لم يبدأ")
    teacher_name = Column(String(200), nullable=True)
    group_name = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)  # Admin notes (visible to student only if flagged)
    notes_visible_to_student = Column(Boolean, default=False)
    city = Column(String(100), default="Riyadh")
    country = Column(String(100), default="Saudi Arabia")
    prayer_method = Column(Integer, default=4)

    # Stats cache (updated by services)
    total_pages_memorized = Column(Float, default=0.0)
    total_pages_revised = Column(Float, default=0.0)
    average_grade = Column(Float, nullable=True)
    completed_juz_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="student_profile")
    progress_records = relationship("MemorizationProgress", back_populates="student", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="student", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="student", cascade="all, delete-orphan")
    plans = relationship("MemorizationPlan", back_populates="student", cascade="all, delete-orphan")
    goals = relationship("StudentGoal", back_populates="student", cascade="all, delete-orphan")
    tasbeeh_sessions = relationship("TasbeehSession", back_populates="student", cascade="all, delete-orphan")
    adhkar_progress = relationship("AdhkarProgress", back_populates="student", cascade="all, delete-orphan")


# ───────────────────────────── Memorization ─────────────────────────────

class MemorizationProgress(Base):
    """Historical progress records – never overwrite old ones unnecessarily."""
    __tablename__ = "memorization_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    juz = Column(Integer, nullable=False)
    surah = Column(Integer, nullable=False)
    from_ayah = Column(Integer, nullable=False)
    to_ayah = Column(Integer, nullable=False)
    pages_amount = Column(Float, default=0.0)  # approximate pages
    status = Column(SAEnum(ProgressStatus), default=ProgressStatus.COMPLETED)
    is_revision = Column(Boolean, default=False)
    record_date = Column(Date, default=date.today)
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="progress_records")


class MemorizationPlan(Base):
    __tablename__ = "memorization_plans"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=True)
    frequency_days = Column(Integer, default=1)  # every N days
    memorize_pages = Column(Float, default=1.0)
    revision_pages = Column(Float, default=2.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="plans")
    tasks = relationship("MemorizationTask", back_populates="plan", cascade="all, delete-orphan")


class MemorizationTask(Base):
    __tablename__ = "memorization_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("memorization_plans.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    task_date = Column(Date, nullable=False)
    memorize_pages = Column(Float, default=0.0)
    revision_pages = Column(Float, default=0.0)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.NOT_STARTED)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    plan = relationship("MemorizationPlan", back_populates="tasks")


class StudentGoal(Base):
    __tablename__ = "student_goals"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(300), nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    unit = Column(String(50), default="صفحة")  # pages, juz, etc.
    deadline = Column(Date, nullable=True)
    status = Column(SAEnum(GoalStatus), default=GoalStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="goals")


# ───────────────────────────── Exams & Grades ─────────────────────────────

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    exam_type = Column(SAEnum(ExamType), default=ExamType.GENERAL)
    exam_date = Column(Date, nullable=False)
    juz = Column(Integer, nullable=True)
    surah = Column(Integer, nullable=True)
    from_ayah = Column(Integer, nullable=True)
    to_ayah = Column(Integer, nullable=True)
    grade = Column(Float, nullable=False)
    max_grade = Column(Float, default=100.0)
    teacher_notes = Column(Text, nullable=True)
    general_notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="exams")


# ───────────────────────────── Schedule & Events ─────────────────────────────

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=True, index=True)  # null = group/all
    group_name = Column(String(100), nullable=True)

    title = Column(String(200), nullable=False)
    schedule_type = Column(String(50), default="class")  # memorization, revision, exam, class, individual, group
    schedule_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=True)  # HH:MM
    end_time = Column(String(10), nullable=True)
    location = Column(String(200), nullable=True)
    teacher_name = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="schedules")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=True)
    end_time = Column(String(10), nullable=True)
    location = Column(String(200), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    is_important = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    publish_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ───────────────────────────── Notifications ─────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


# ───────────────────────────── Adhkar & Tasbeeh ─────────────────────────────

class AdhkarCategory(Base):
    __tablename__ = "adhkar_categories"

    id = Column(Integer, primary_key=True, index=True)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=True)
    order = Column(Integer, default=0)

    items = relationship("AdhkarItem", back_populates="category", cascade="all, delete-orphan")


class AdhkarItem(Base):
    __tablename__ = "adhkar_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("adhkar_categories.id", ondelete="CASCADE"), nullable=False)

    text_ar = Column(Text, nullable=False)
    repetitions = Column(Integer, default=1)
    source = Column(String(200), nullable=True)
    explanation = Column(Text, nullable=True)
    order = Column(Integer, default=0)

    category = relationship("AdhkarCategory", back_populates="items")


class AdhkarProgress(Base):
    __tablename__ = "adhkar_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    adhkar_item_id = Column(Integer, ForeignKey("adhkar_items.id", ondelete="CASCADE"), nullable=False)
    progress_date = Column(Date, default=date.today)
    count = Column(Integer, default=0)
    completed = Column(Boolean, default=False)

    student = relationship("StudentProfile", back_populates="adhkar_progress")

    __table_args__ = (UniqueConstraint("student_id", "adhkar_item_id", "progress_date", name="uq_adhkar_daily"),)


class TasbeehSession(Base):
    __tablename__ = "tasbeeh_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    target = Column(Integer, default=33)
    count = Column(Integer, default=0)
    dhikr_text = Column(String(200), default="سبحان الله")
    completed = Column(Boolean, default=False)
    session_date = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="tasbeeh_sessions")


# ───────────────────────────── Settings & Audit ─────────────────────────────

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
