"""
Memorization progress tracking + personal plans + goals.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, StudentProfile, MemorizationProgress, ProgressStatus,
    MemorizationPlan, MemorizationTask, TaskStatus, StudentGoal, GoalStatus,
    AuditLog, Notification
)
from app.schemas import ProgressCreate, ProgressOut, PlanCreate, GoalCreate, MessageResponse
from app.security import require_admin, require_student, get_current_user

router = APIRouter(prefix="/api/progress", tags=["Progress"])


# ─── Progress records ───

@router.post("/", response_model=ProgressOut, status_code=201)
async def add_progress(
    body: ProgressCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin records memorization / revision progress for a student."""
    profile = db.query(StudentProfile).filter(StudentProfile.id == body.student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    try:
        st = ProgressStatus(body.status)
    except ValueError:
        st = ProgressStatus.COMPLETED

    record = MemorizationProgress(
        student_id=body.student_id,
        juz=body.juz,
        surah=body.surah,
        from_ayah=body.from_ayah,
        to_ayah=body.to_ayah,
        pages_amount=body.pages_amount,
        status=st,
        is_revision=body.is_revision,
        record_date=body.record_date or date.today(),
        notes=body.notes,
        created_by_id=admin.id,
    )
    db.add(record)

    # Update current position & totals
    if not body.is_revision:
        profile.current_juz = body.juz
        profile.current_surah = body.surah
        profile.current_ayah = body.to_ayah
        profile.total_pages_memorized = (profile.total_pages_memorized or 0) + body.pages_amount
        if body.juz > (profile.completed_juz_count or 0) and body.to_ayah >= 1:
            # simple heuristic: if finishing last surah of juz roughly
            pass
    else:
        profile.total_pages_revised = (profile.total_pages_revised or 0) + body.pages_amount

    db.add(Notification(
        user_id=profile.user_id,
        title="تحديث تقدم الحفظ",
        message=f"{'مراجعة' if body.is_revision else 'حفظ'} جزء {body.juz} سورة {body.surah} آية {body.from_ayah}-{body.to_ayah}",
        link="/student/progress",
    ))
    db.add(AuditLog(
        user_id=admin.id,
        action="PROGRESS_ADDED",
        entity_type="progress",
        details=f"Student {body.student_id}: Juz {body.juz} Surah {body.surah}",
    ))
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "student_id": record.student_id,
        "juz": record.juz,
        "surah": record.surah,
        "from_ayah": record.from_ayah,
        "to_ayah": record.to_ayah,
        "pages_amount": record.pages_amount,
        "status": record.status.value,
        "is_revision": record.is_revision,
        "record_date": record.record_date,
        "notes": record.notes,
        "created_at": record.created_at,
    }


@router.get("/student/{student_id}")
async def student_progress_history(
    student_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    records = db.query(MemorizationProgress).filter(
        MemorizationProgress.student_id == student_id
    ).order_by(MemorizationProgress.record_date.desc()).all()
    return [
        {
            "id": r.id, "juz": r.juz, "surah": r.surah,
            "from_ayah": r.from_ayah, "to_ayah": r.to_ayah,
            "pages_amount": r.pages_amount, "status": r.status.value,
            "is_revision": r.is_revision, "record_date": r.record_date.isoformat(),
            "notes": r.notes,
        }
        for r in records
    ]


@router.get("/my")
async def my_progress(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    records = db.query(MemorizationProgress).filter(
        MemorizationProgress.student_id == profile.id
    ).order_by(MemorizationProgress.record_date.desc()).limit(50).all()

    # Rough overall % (30 juz)
    overall_pct = min(100, round((profile.total_pages_memorized or 0) / 604 * 100, 1))

    return {
        "current_juz": profile.current_juz,
        "current_surah": profile.current_surah,
        "current_ayah": profile.current_ayah,
        "total_pages_memorized": profile.total_pages_memorized,
        "total_pages_revised": profile.total_pages_revised,
        "completed_juz_count": profile.completed_juz_count,
        "overall_percentage": overall_pct,
        "history": [
            {
                "id": r.id, "juz": r.juz, "surah": r.surah,
                "from_ayah": r.from_ayah, "to_ayah": r.to_ayah,
                "pages_amount": r.pages_amount, "is_revision": r.is_revision,
                "record_date": r.record_date.isoformat(), "notes": r.notes,
            }
            for r in records
        ],
    }


# ─── Personal memorization plans ───

@router.post("/plans", status_code=201)
async def create_plan(
    body: PlanCreate,
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Student creates a personal memorization plan; tasks are auto-generated."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")

    plan = MemorizationPlan(
        student_id=profile.id,
        title=body.title,
        start_date=body.start_date,
        target_date=body.target_date,
        frequency_days=max(1, body.frequency_days),
        memorize_pages=body.memorize_pages,
        revision_pages=body.revision_pages,
        is_active=True,
    )
    db.add(plan)
    db.flush()

    # Generate tasks for ~30 days or until target
    end = body.target_date or (body.start_date + timedelta(days=30))
    current_date = body.start_date
    while current_date <= end:
        task = MemorizationTask(
            plan_id=plan.id,
            student_id=profile.id,
            task_date=current_date,
            memorize_pages=body.memorize_pages,
            revision_pages=body.revision_pages,
            status=TaskStatus.NOT_STARTED,
        )
        db.add(task)
        current_date += timedelta(days=plan.frequency_days)

    db.commit()
    db.refresh(plan)
    tasks = db.query(MemorizationTask).filter(MemorizationTask.plan_id == plan.id).all()
    return {
        "id": plan.id,
        "title": plan.title,
        "start_date": plan.start_date.isoformat(),
        "target_date": plan.target_date.isoformat() if plan.target_date else None,
        "frequency_days": plan.frequency_days,
        "memorize_pages": plan.memorize_pages,
        "revision_pages": plan.revision_pages,
        "tasks_count": len(tasks),
        "tasks": [
            {
                "id": t.id, "date": t.task_date.isoformat(),
                "memorize_pages": t.memorize_pages, "revision_pages": t.revision_pages,
                "status": t.status.value,
            }
            for t in tasks
        ],
    }


@router.get("/plans/my")
async def my_plans(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    plans = db.query(MemorizationPlan).filter(
        MemorizationPlan.student_id == profile.id,
        MemorizationPlan.is_active == True,
    ).all()
    result = []
    for p in plans:
        tasks = db.query(MemorizationTask).filter(MemorizationTask.plan_id == p.id).all()
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        result.append({
            "id": p.id, "title": p.title,
            "start_date": p.start_date.isoformat(),
            "tasks_total": len(tasks),
            "tasks_completed": completed,
            "progress_pct": round(completed / len(tasks) * 100, 1) if tasks else 0,
        })
    return result


@router.get("/tasks/today")
async def today_tasks(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    today = date.today()
    tasks = db.query(MemorizationTask).filter(
        MemorizationTask.student_id == profile.id,
        MemorizationTask.task_date == today,
    ).all()
    return [
        {
            "id": t.id,
            "memorize_pages": t.memorize_pages,
            "revision_pages": t.revision_pages,
            "status": t.status.value,
            "date": t.task_date.isoformat(),
        }
        for t in tasks
    ]


@router.post("/tasks/{task_id}/complete", response_model=MessageResponse)
async def complete_task(
    task_id: int,
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    task = db.query(MemorizationTask).filter(MemorizationTask.id == task_id).first()
    if not task or not profile or task.student_id != profile.id:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    profile.total_pages_memorized = (profile.total_pages_memorized or 0) + (task.memorize_pages or 0)
    profile.total_pages_revised = (profile.total_pages_revised or 0) + (task.revision_pages or 0)
    db.commit()
    return MessageResponse(message="تم إكمال المهمة بنجاح ✓")


@router.post("/tasks/{task_id}/start", response_model=MessageResponse)
async def start_task(
    task_id: int,
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    task = db.query(MemorizationTask).filter(MemorizationTask.id == task_id).first()
    if not task or not profile or task.student_id != profile.id:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    task.status = TaskStatus.IN_PROGRESS
    db.commit()
    return MessageResponse(message="تم بدء المهمة")


# ─── Goals ───

@router.post("/goals", status_code=201)
async def create_goal(
    body: GoalCreate,
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    goal = StudentGoal(
        student_id=profile.id,
        title=body.title,
        target_value=body.target_value,
        unit=body.unit,
        deadline=body.deadline,
        status=GoalStatus.ACTIVE,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return {
        "id": goal.id, "title": goal.title,
        "target_value": goal.target_value, "current_value": goal.current_value,
        "unit": goal.unit, "deadline": goal.deadline.isoformat() if goal.deadline else None,
        "status": goal.status.value,
        "percentage": 0,
    }


@router.get("/goals/my")
async def my_goals(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        return []
    goals = db.query(StudentGoal).filter(StudentGoal.student_id == profile.id).all()
    return [
        {
            "id": g.id, "title": g.title,
            "target_value": g.target_value, "current_value": g.current_value,
            "unit": g.unit,
            "deadline": g.deadline.isoformat() if g.deadline else None,
            "status": g.status.value,
            "percentage": min(100, round(g.current_value / g.target_value * 100, 1)) if g.target_value else 0,
        }
        for g in goals
    ]
