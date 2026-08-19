"""
Announcements, Events, Schedules, Notifications, Adhkar, Tasbeeh, Prayer times.
"""
from datetime import datetime, date
from typing import Optional, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, StudentProfile, Announcement, Event, Schedule, Notification,
    AdhkarCategory, AdhkarItem, AdhkarProgress, TasbeehSession, AuditLog
)
from app.schemas import (
    AnnouncementCreate, AnnouncementOut, EventCreate, EventOut,
    ScheduleCreate, ScheduleOut, NotificationCreate, NotificationOut,
    TasbeehUpdate, MessageResponse
)
from app.security import require_admin, require_student, get_current_user
from app.config import PRAYER_API_BASE, DEFAULT_PRAYER_METHOD

router = APIRouter(prefix="/api", tags=["Content"])


# ─── Announcements ───

@router.get("/announcements", response_model=List[AnnouncementOut])
async def list_announcements(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    q = db.query(Announcement).filter(Announcement.is_published == True)
    items = q.order_by(Announcement.is_important.desc(), Announcement.publish_at.desc()).limit(30).all()
    return items


@router.post("/announcements", response_model=AnnouncementOut, status_code=201)
async def create_announcement(
    body: AnnouncementCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ann = Announcement(
        title=body.title,
        content=body.content,
        is_important=body.is_important,
        is_published=body.is_published,
        created_by_id=admin.id,
    )
    db.add(ann)
    # Notify all active students
    students = db.query(User).filter(User.role == "STUDENT", User.status == "ACTIVE").all()
    for s in students:
        db.add(Notification(
            user_id=s.id,
            title="إعلان جديد" + (" ⭐" if body.is_important else ""),
            message=body.title,
            link="/student",
        ))
    db.add(AuditLog(user_id=admin.id, action="ANNOUNCEMENT_CREATED", details=body.title))
    db.commit()
    db.refresh(ann)
    return ann


@router.delete("/announcements/{ann_id}", response_model=MessageResponse)
async def delete_announcement(
    ann_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="الإعلان غير موجود")
    db.delete(ann)
    db.commit()
    return MessageResponse(message="تم حذف الإعلان")


# ─── Events ───

@router.get("/events", response_model=List[EventOut])
async def list_events(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    items = db.query(Event).filter(
        Event.is_visible == True,
        Event.event_date >= date.today(),
    ).order_by(Event.event_date).limit(20).all()
    return items


@router.post("/events", response_model=EventOut, status_code=201)
async def create_event(
    body: EventCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ev = Event(**body.model_dump())
    db.add(ev)
    db.add(AuditLog(user_id=admin.id, action="EVENT_CREATED", details=body.title))
    db.commit()
    db.refresh(ev)
    return ev


@router.delete("/events/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="الفعالية غير موجودة")
    db.delete(ev)
    db.commit()
    return MessageResponse(message="تم حذف الفعالية")


# ─── Schedules ───

@router.get("/schedules")
async def list_schedules(
    student_id: Optional[int] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Schedule)
    if student_id:
        q = q.filter(Schedule.student_id == student_id)
    items = q.order_by(Schedule.schedule_date.desc()).limit(50).all()
    return items


@router.get("/schedules/my")
async def my_schedules(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        return []
    items = db.query(Schedule).filter(
        (Schedule.student_id == profile.id) | (Schedule.student_id == None),
        Schedule.schedule_date >= date.today(),
    ).order_by(Schedule.schedule_date).limit(20).all()
    return items


@router.post("/schedules", status_code=201)
async def create_schedule(
    body: ScheduleCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    sch = Schedule(**body.model_dump())
    db.add(sch)
    if body.student_id:
        profile = db.query(StudentProfile).filter(StudentProfile.id == body.student_id).first()
        if profile:
            db.add(Notification(
                user_id=profile.user_id,
                title="موعد جديد",
                message=f"{body.title} - {body.schedule_date}",
                link="/student/schedule",
            ))
    db.commit()
    db.refresh(sch)
    return sch


@router.delete("/schedules/{sch_id}", response_model=MessageResponse)
async def delete_schedule(
    sch_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    sch = db.query(Schedule).filter(Schedule.id == sch_id).first()
    if not sch:
        raise HTTPException(status_code=404, detail="الجدول غير موجود")
    db.delete(sch)
    db.commit()
    return MessageResponse(message="تم حذف الموعد")


# ─── Notifications ───

@router.get("/notifications", response_model=List[NotificationOut])
async def my_notifications(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(Notification).filter(
        Notification.user_id == current.id
    ).order_by(Notification.created_at.desc()).limit(40).all()
    return items


@router.post("/notifications/read/{notif_id}", response_model=MessageResponse)
async def mark_read(
    notif_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current.id
    ).first()
    if n:
        n.is_read = True
        db.commit()
    return MessageResponse(message="تم")


@router.post("/notifications/read-all", response_model=MessageResponse)
async def mark_all_read(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return MessageResponse(message="تم تعليم الكل كمقروء")


@router.post("/notifications/send", response_model=MessageResponse)
async def send_notification(
    body: NotificationCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    targets = []
    if body.user_id:
        targets = [body.user_id]
    elif body.user_ids:
        targets = body.user_ids
    else:
        # all active students
        targets = [u.id for u in db.query(User).filter(User.role == "STUDENT", User.status == "ACTIVE").all()]

    for uid in targets:
        db.add(Notification(
            user_id=uid,
            title=body.title,
            message=body.message,
            link=body.link,
        ))
    db.commit()
    return MessageResponse(message=f"تم إرسال الإشعار إلى {len(targets)} مستخدم")


# ─── Adhkar ───

@router.get("/adhkar")
async def list_adhkar(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    cats = db.query(AdhkarCategory).order_by(AdhkarCategory.order).all()
    result = []
    for c in cats:
        items = db.query(AdhkarItem).filter(AdhkarItem.category_id == c.id).order_by(AdhkarItem.order).all()
        result.append({
            "id": c.id,
            "name_ar": c.name_ar,
            "name_en": c.name_en,
            "items": [
                {
                    "id": i.id,
                    "text_ar": i.text_ar,
                    "repetitions": i.repetitions,
                    "source": i.source,
                    "explanation": i.explanation,
                }
                for i in items
            ],
        })
    return result


# ─── Tasbeeh ───

@router.post("/tasbeeh", status_code=201)
async def save_tasbeeh(
    body: TasbeehUpdate,
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    session = TasbeehSession(
        student_id=profile.id,
        target=body.target,
        count=body.count,
        dhikr_text=body.dhikr_text,
        completed=body.count >= body.target,
    )
    db.add(session)
    db.commit()
    return {"id": session.id, "completed": session.completed}


@router.get("/tasbeeh/history")
async def tasbeeh_history(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        return []
    sessions = db.query(TasbeehSession).filter(
        TasbeehSession.student_id == profile.id
    ).order_by(TasbeehSession.session_date.desc()).limit(20).all()
    return [
        {
            "id": s.id, "target": s.target, "count": s.count,
            "dhikr_text": s.dhikr_text, "completed": s.completed,
            "date": s.session_date.isoformat(),
        }
        for s in sessions
    ]


# ─── Prayer Times (Aladhan API) ───

@router.get("/prayer-times")
async def prayer_times(
    city: str = Query("Riyadh"),
    country: str = Query("Saudi Arabia"),
    method: int = Query(DEFAULT_PRAYER_METHOD),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch prayer times from Aladhan API. Saves preference for students."""
    # Save preference if student
    if current.role.value == "STUDENT":
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
        if profile:
            profile.city = city
            profile.country = country
            profile.prayer_method = method
            db.commit()

    url = f"{PRAYER_API_BASE}/timingsByCity"
    params = {"city": city, "country": country, "method": method}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 200:
                raise HTTPException(status_code=502, detail="فشل جلب أوقات الصلاة")
            timings = data["data"]["timings"]
            date_info = data["data"]["date"]
            return {
                "city": city,
                "country": country,
                "method": method,
                "date": date_info.get("readable"),
                "hijri": date_info.get("hijri", {}).get("date"),
                "timings": {
                    "Fajr": timings.get("Fajr", "").split(" ")[0],
                    "Sunrise": timings.get("Sunrise", "").split(" ")[0],
                    "Dhuhr": timings.get("Dhuhr", "").split(" ")[0],
                    "Asr": timings.get("Asr", "").split(" ")[0],
                    "Maghrib": timings.get("Maghrib", "").split(" ")[0],
                    "Isha": timings.get("Isha", "").split(" ")[0],
                },
            }
    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="تعذر الاتصال بخدمة أوقات الصلاة. حاول لاحقاً.",
        )


@router.get("/prayer-times/my")
async def my_prayer_preference(
    current: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current.id).first()
    if not profile:
        return {"city": "Riyadh", "country": "Saudi Arabia", "method": 4}
    return {
        "city": profile.city or "Riyadh",
        "country": profile.country or "Saudi Arabia",
        "method": profile.prayer_method or 4,
    }
