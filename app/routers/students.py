"""
Student management – Admin only for CRUD, students see own profile.
"""
from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.models import User, StudentProfile, UserRole, AccountStatus, AuditLog, Exam, MemorizationProgress
from app.schemas import (
    StudentCreate, StudentUpdate, StudentOut, PasswordResetRequest, MessageResponse
)
from app.security import require_admin, get_current_user, hash_password, require_student

router = APIRouter(prefix="/api/students", tags=["Students"])


def _student_to_out(profile: StudentProfile) -> dict:
    """Map StudentProfile + User to StudentOut dict."""
    u = profile.user
    return {
        "id": profile.id,
        "user_id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "phone": u.phone,
        "status": u.status.value,
        "parent_name": profile.parent_name,
        "parent_phone": profile.parent_phone,
        "date_of_birth": profile.date_of_birth,
        "enrollment_date": profile.enrollment_date,
        "current_juz": profile.current_juz,
        "current_surah": profile.current_surah,
        "current_ayah": profile.current_ayah,
        "memorization_status": profile.memorization_status,
        "revision_status": profile.revision_status,
        "teacher_name": profile.teacher_name,
        "group_name": profile.group_name,
        "notes": profile.notes,
        "notes_visible_to_student": profile.notes_visible_to_student,
        "total_pages_memorized": profile.total_pages_memorized or 0,
        "total_pages_revised": profile.total_pages_revised or 0,
        "average_grade": profile.average_grade,
        "completed_juz_count": profile.completed_juz_count or 0,
        "city": profile.city,
        "country": profile.country,
        "created_at": profile.created_at,
    }


@router.get("/", response_model=List[StudentOut])
async def list_students(
    q: Optional[str] = Query(None, description="Search name/username"),
    juz: Optional[int] = None,
    group: Optional[str] = None,
    teacher: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List/search students (Admin only)."""
    query = db.query(StudentProfile).join(User).options(joinedload(StudentProfile.user))

    if q:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{q}%"),
                User.username.ilike(f"%{q}%"),
            )
        )
    if juz is not None:
        query = query.filter(StudentProfile.current_juz == juz)
    if group:
        query = query.filter(StudentProfile.group_name.ilike(f"%{group}%"))
    if teacher:
        query = query.filter(StudentProfile.teacher_name.ilike(f"%{teacher}%"))
    if status_filter:
        try:
            st = AccountStatus(status_filter)
            query = query.filter(User.status == st)
        except ValueError:
            pass

    profiles = query.order_by(User.full_name).offset(skip).limit(limit).all()
    return [_student_to_out(p) for p in profiles]


@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(
    body: StudentCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new student account (Admin only)."""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود مسبقاً")

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role=UserRole.STUDENT,
        status=AccountStatus.ACTIVE,
        full_name=body.full_name,
        phone=body.phone,
    )
    db.add(user)
    db.flush()

    profile = StudentProfile(
        user_id=user.id,
        parent_name=body.parent_name,
        parent_phone=body.parent_phone,
        date_of_birth=body.date_of_birth,
        enrollment_date=date.today(),
        current_juz=body.current_juz,
        current_surah=body.current_surah,
        teacher_name=body.teacher_name,
        group_name=body.group_name,
        notes=body.notes,
    )
    db.add(profile)

    db.add(AuditLog(
        user_id=admin.id,
        action="STUDENT_CREATED",
        entity_type="student",
        entity_id=user.id,
        details=f"Created student {body.username} ({body.full_name})",
    ))
    db.commit()
    db.refresh(profile)
    return _student_to_out(profile)


@router.get("/me", response_model=StudentOut)
async def my_profile(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Student views own profile."""
    profile = db.query(StudentProfile).options(joinedload(StudentProfile.user)).filter(
        StudentProfile.user_id == current.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف الشخصي غير موجود")
    out = _student_to_out(profile)
    # Hide admin-only notes unless marked visible
    if not profile.notes_visible_to_student:
        out["notes"] = None
    return out


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin views a student profile."""
    profile = db.query(StudentProfile).options(joinedload(StudentProfile.user)).filter(
        StudentProfile.id == student_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return _student_to_out(profile)


@router.put("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: int,
    body: StudentUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update student profile (Admin)."""
    profile = db.query(StudentProfile).options(joinedload(StudentProfile.user)).filter(
        StudentProfile.id == student_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    user = profile.user
    data = body.model_dump(exclude_unset=True)

    if "full_name" in data:
        user.full_name = data.pop("full_name")
    if "phone" in data:
        user.phone = data.pop("phone")
    if "status" in data:
        user.status = AccountStatus(data.pop("status"))

    for k, v in data.items():
        if hasattr(profile, k):
            setattr(profile, k, v)

    user.updated_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=admin.id,
        action="STUDENT_UPDATED",
        entity_type="student",
        entity_id=student_id,
        details=f"Updated student {user.username}",
    ))
    db.commit()
    db.refresh(profile)
    return _student_to_out(profile)


@router.post("/{student_id}/reset-password", response_model=MessageResponse)
async def reset_password(
    student_id: int,
    body: PasswordResetRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin resets a student's password."""
    profile = db.query(StudentProfile).options(joinedload(StudentProfile.user)).filter(
        StudentProfile.id == student_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    profile.user.password_hash = hash_password(body.new_password)
    profile.user.must_change_password = True
    profile.user.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=admin.id,
        action="PASSWORD_RESET",
        entity_type="student",
        entity_id=student_id,
        details=f"Password reset for {profile.user.username}",
    ))
    db.commit()
    return MessageResponse(message="تم إعادة تعيين كلمة المرور بنجاح")


@router.post("/{student_id}/toggle-status", response_model=MessageResponse)
async def toggle_status(
    student_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate / deactivate student account."""
    profile = db.query(StudentProfile).options(joinedload(StudentProfile.user)).filter(
        StudentProfile.id == student_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    user = profile.user
    if user.status == AccountStatus.ACTIVE:
        user.status = AccountStatus.INACTIVE
        msg = "تم تعطيل الحساب"
    else:
        user.status = AccountStatus.ACTIVE
        msg = "تم تفعيل الحساب"

    db.add(AuditLog(
        user_id=admin.id,
        action="STATUS_CHANGED",
        entity_type="student",
        entity_id=student_id,
        details=f"{user.username} → {user.status.value}",
    ))
    db.commit()
    return MessageResponse(message=msg)


@router.delete("/{student_id}", response_model=MessageResponse)
async def delete_student(
    student_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Permanently delete a student and related data."""
    profile = db.query(StudentProfile).options(joinedload(StudentProfile.user)).filter(
        StudentProfile.id == student_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    username = profile.user.username
    db.delete(profile.user)  # cascades to profile and related
    db.add(AuditLog(
        user_id=admin.id,
        action="STUDENT_DELETED",
        entity_type="student",
        entity_id=student_id,
        details=f"Deleted student {username}",
    ))
    db.commit()
    return MessageResponse(message=f"تم حذف الطالب {username}")


@router.get("/{student_id}/stats")
async def student_stats(
    student_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Detailed stats for a student (Admin view)."""
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    exams = db.query(Exam).filter(Exam.student_id == student_id).all()
    grades = [e.grade for e in exams] if exams else []
    progress = db.query(MemorizationProgress).filter(
        MemorizationProgress.student_id == student_id
    ).order_by(MemorizationProgress.record_date.desc()).limit(20).all()

    return {
        "student_id": student_id,
        "current_juz": profile.current_juz,
        "current_surah": profile.current_surah,
        "total_pages_memorized": profile.total_pages_memorized,
        "total_pages_revised": profile.total_pages_revised,
        "completed_juz_count": profile.completed_juz_count,
        "exams_count": len(exams),
        "average_grade": sum(grades) / len(grades) if grades else None,
        "highest_grade": max(grades) if grades else None,
        "lowest_grade": min(grades) if grades else None,
        "recent_progress": [
            {
                "juz": p.juz, "surah": p.surah,
                "from_ayah": p.from_ayah, "to_ayah": p.to_ayah,
                "is_revision": p.is_revision, "date": p.record_date.isoformat(),
            }
            for p in progress
        ],
    }
