"""
Dashboard statistics for Admin and Student.
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    User, StudentProfile, Exam, MemorizationProgress, Schedule,
    Event, Announcement, Notification, AccountStatus, UserRole
)
from app.security import require_admin, require_student

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/admin")
async def admin_dashboard(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_students = db.query(StudentProfile).count()
    active_students = db.query(StudentProfile).join(User).filter(
        User.status == AccountStatus.ACTIVE
    ).count()
    total_exams = db.query(Exam).count()
    avg_grade = db.query(func.avg(Exam.grade)).scalar()

    # Top progress students
    top = db.query(StudentProfile).join(User).order_by(
        StudentProfile.total_pages_memorized.desc()
    ).limit(5).all()

    # Need attention: low average or no recent progress
    need_attention = db.query(StudentProfile).join(User).filter(
        User.status == AccountStatus.ACTIVE,
        (StudentProfile.average_grade < 60) | (StudentProfile.average_grade == None),
    ).limit(5).all()

    today = date.today()
    today_schedules = db.query(Schedule).filter(Schedule.schedule_date == today).limit(10).all()
    upcoming_exams = db.query(Exam).filter(Exam.exam_date >= today).order_by(Exam.exam_date).limit(5).all()
    upcoming_events = db.query(Event).filter(
        Event.event_date >= today, Event.is_visible == True
    ).order_by(Event.event_date).limit(5).all()
    recent_anns = db.query(Announcement).filter(
        Announcement.is_published == True
    ).order_by(Announcement.publish_at.desc()).limit(5).all()

    return {
        "stats": {
            "total_students": total_students,
            "active_students": active_students,
            "total_exams": total_exams,
            "average_grade": round(avg_grade, 1) if avg_grade else None,
        },
        "top_students": [
            {
                "id": p.id, "name": p.user.full_name,
                "pages": p.total_pages_memorized, "juz": p.current_juz,
            }
            for p in top
        ],
        "need_attention": [
            {
                "id": p.id, "name": p.user.full_name,
                "avg_grade": p.average_grade, "juz": p.current_juz,
            }
            for p in need_attention
        ],
        "today_schedules": [
            {"id": s.id, "title": s.title, "time": s.start_time, "student_id": s.student_id}
            for s in today_schedules
        ],
        "upcoming_exams": [
            {"id": e.id, "title": e.title, "date": e.exam_date.isoformat(), "student_id": e.student_id}
            for e in upcoming_exams
        ],
        "upcoming_events": [
            {"id": e.id, "title": e.title, "date": e.event_date.isoformat()}
            for e in upcoming_events
        ],
        "recent_announcements": [
            {"id": a.id, "title": a.title, "important": a.is_important}
            for a in recent_anns
        ],
    }


@router.get("/student")
async def student_dashboard(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        return {"error": "profile not found"}

    today = date.today()
    from app.models import MemorizationTask, TaskStatus
    today_tasks = db.query(MemorizationTask).filter(
        MemorizationTask.student_id == profile.id,
        MemorizationTask.task_date == today,
    ).all()

    recent_exams = db.query(Exam).filter(
        Exam.student_id == profile.id
    ).order_by(Exam.exam_date.desc()).limit(5).all()

    next_schedule = db.query(Schedule).filter(
        (Schedule.student_id == profile.id) | (Schedule.student_id == None),
        Schedule.schedule_date >= today,
    ).order_by(Schedule.schedule_date).first()

    anns = db.query(Announcement).filter(
        Announcement.is_published == True
    ).order_by(Announcement.publish_at.desc()).limit(5).all()

    events = db.query(Event).filter(
        Event.is_visible == True, Event.event_date >= today
    ).order_by(Event.event_date).limit(5).all()

    unread = db.query(Notification).filter(
        Notification.user_id == current.id, Notification.is_read == False
    ).count()

    overall_pct = min(100, round((profile.total_pages_memorized or 0) / 604 * 100, 1))

    return {
        "welcome_name": current.full_name,
        "current_juz": profile.current_juz,
        "current_surah": profile.current_surah,
        "overall_percentage": overall_pct,
        "total_pages_memorized": profile.total_pages_memorized or 0,
        "total_pages_revised": profile.total_pages_revised or 0,
        "average_grade": profile.average_grade,
        "latest_grade": recent_exams[0].grade if recent_exams else None,
        "unread_notifications": unread,
        "today_tasks": [
            {
                "id": t.id,
                "memorize_pages": t.memorize_pages,
                "revision_pages": t.revision_pages,
                "status": t.status.value,
            }
            for t in today_tasks
        ],
        "next_schedule": {
            "title": next_schedule.title,
            "date": next_schedule.schedule_date.isoformat(),
            "time": next_schedule.start_time,
        } if next_schedule else None,
        "recent_grades": [
            {"title": e.title, "grade": e.grade, "max": e.max_grade, "date": e.exam_date.isoformat()}
            for e in recent_exams
        ],
        "announcements": [
            {"id": a.id, "title": a.title, "important": a.is_important, "content": a.content[:100]}
            for a in anns
        ],
        "events": [
            {"id": e.id, "title": e.title, "date": e.event_date.isoformat()}
            for e in events
        ],
        "city": profile.city or "Riyadh",
        "country": profile.country or "Saudi Arabia",
    }
