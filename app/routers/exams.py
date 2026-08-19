"""
Exams and grades management.
"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Exam, StudentProfile, ExamType, AuditLog, Notification
from app.schemas import ExamCreate, ExamOut, MessageResponse
from app.security import require_admin, require_student, get_current_user

router = APIRouter(prefix="/api/exams", tags=["Exams"])


def _exam_out(e: Exam) -> dict:
    pct = round((e.grade / e.max_grade) * 100, 1) if e.max_grade else None
    return {
        "id": e.id,
        "student_id": e.student_id,
        "title": e.title,
        "exam_type": e.exam_type.value if hasattr(e.exam_type, "value") else str(e.exam_type),
        "exam_date": e.exam_date,
        "juz": e.juz,
        "surah": e.surah,
        "from_ayah": e.from_ayah,
        "to_ayah": e.to_ayah,
        "grade": e.grade,
        "max_grade": e.max_grade,
        "percentage": pct,
        "teacher_notes": e.teacher_notes,
        "general_notes": e.general_notes,
        "created_at": e.created_at,
    }


@router.get("/", response_model=List[ExamOut])
async def list_exams(
    student_id: Optional[int] = None,
    exam_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin lists exams with optional filters."""
    q = db.query(Exam)
    if student_id:
        q = q.filter(Exam.student_id == student_id)
    if exam_type:
        try:
            q = q.filter(Exam.exam_type == ExamType(exam_type))
        except ValueError:
            pass
    exams = q.order_by(Exam.exam_date.desc()).offset(skip).limit(limit).all()
    return [_exam_out(e) for e in exams]


@router.post("/", response_model=ExamOut, status_code=201)
async def create_exam(
    body: ExamCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin creates an exam / grade for a student."""
    profile = db.query(StudentProfile).filter(StudentProfile.id == body.student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    try:
        et = ExamType(body.exam_type)
    except ValueError:
        et = ExamType.GENERAL

    exam = Exam(
        student_id=body.student_id,
        title=body.title,
        exam_type=et,
        exam_date=body.exam_date,
        juz=body.juz,
        surah=body.surah,
        from_ayah=body.from_ayah,
        to_ayah=body.to_ayah,
        grade=body.grade,
        max_grade=body.max_grade,
        teacher_notes=body.teacher_notes,
        general_notes=body.general_notes,
        created_by_id=admin.id,
    )
    db.add(exam)

    # Update average grade
    all_exams = db.query(Exam).filter(Exam.student_id == body.student_id).all()
    grades = [e.grade for e in all_exams] + [body.grade]
    profile.average_grade = sum(grades) / len(grades)

    # Notify student
    db.add(Notification(
        user_id=profile.user_id,
        title="نتيجة اختبار جديدة",
        message=f"تم تسجيل درجة {body.grade}/{body.max_grade} في اختبار: {body.title}",
        link="/student/grades",
    ))

    db.add(AuditLog(
        user_id=admin.id,
        action="EXAM_CREATED",
        entity_type="exam",
        details=f"Exam '{body.title}' grade {body.grade} for student {body.student_id}",
    ))
    db.commit()
    db.refresh(exam)
    return _exam_out(exam)


@router.get("/my", response_model=List[ExamOut])
async def my_exams(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Student views own grades."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    exams = db.query(Exam).filter(Exam.student_id == profile.id).order_by(Exam.exam_date.desc()).all()
    return [_exam_out(e) for e in exams]


@router.get("/my/summary")
async def my_grades_summary(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Student grade statistics."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    exams = db.query(Exam).filter(Exam.student_id == profile.id).all()
    grades = [e.grade for e in exams]
    return {
        "count": len(exams),
        "average": round(sum(grades) / len(grades), 1) if grades else None,
        "highest": max(grades) if grades else None,
        "lowest": min(grades) if grades else None,
        "exams": [_exam_out(e) for e in sorted(exams, key=lambda x: x.exam_date, reverse=True)],
    }


@router.put("/{exam_id}", response_model=ExamOut)
async def update_exam(
    exam_id: int,
    body: ExamCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="الاختبار غير موجود")

    exam.title = body.title
    try:
        exam.exam_type = ExamType(body.exam_type)
    except ValueError:
        pass
    exam.exam_date = body.exam_date
    exam.juz = body.juz
    exam.surah = body.surah
    exam.from_ayah = body.from_ayah
    exam.to_ayah = body.to_ayah
    exam.grade = body.grade
    exam.max_grade = body.max_grade
    exam.teacher_notes = body.teacher_notes
    exam.general_notes = body.general_notes
    exam.updated_at = datetime.utcnow()

    # Recalc average
    profile = db.query(StudentProfile).filter(StudentProfile.id == exam.student_id).first()
    if profile:
        all_e = db.query(Exam).filter(Exam.student_id == exam.student_id).all()
        grades = [e.grade for e in all_e]
        profile.average_grade = sum(grades) / len(grades) if grades else None

    db.add(AuditLog(user_id=admin.id, action="EXAM_UPDATED", entity_type="exam", entity_id=exam_id))
    db.commit()
    db.refresh(exam)
    return _exam_out(exam)


@router.delete("/{exam_id}", response_model=MessageResponse)
async def delete_exam(
    exam_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="الاختبار غير موجود")
    sid = exam.student_id
    db.delete(exam)

    profile = db.query(StudentProfile).filter(StudentProfile.id == sid).first()
    if profile:
        remaining = db.query(Exam).filter(Exam.student_id == sid).all()
        grades = [e.grade for e in remaining]
        profile.average_grade = sum(grades) / len(grades) if grades else None

    db.add(AuditLog(user_id=admin.id, action="EXAM_DELETED", entity_type="exam", entity_id=exam_id))
    db.commit()
    return MessageResponse(message="تم حذف الاختبار")
