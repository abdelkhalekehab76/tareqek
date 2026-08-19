"""
Seed initial data: Admin account + sample Adhkar + settings.
Run automatically on startup if DB is empty.
"""
from datetime import date
from sqlalchemy.orm import Session

from app.models import (
    User, UserRole, AccountStatus, StudentProfile,
    AdhkarCategory, AdhkarItem, Setting, Announcement
)
from app.security import hash_password
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_FULL_NAME


def seed_admin(db: Session) -> None:
    """Create the initial admin account if it does not exist."""
    existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
    if existing:
        return

    admin = User(
        username=ADMIN_USERNAME,
        password_hash=hash_password(ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        status=AccountStatus.ACTIVE,
        full_name=ADMIN_FULL_NAME,
        must_change_password=True,  # force change after first login
    )
    db.add(admin)
    db.commit()
    print(f"[SEED] Admin account created: {ADMIN_USERNAME}")


def seed_adhkar(db: Session) -> None:
    """Seed common Adhkar categories and items if empty."""
    if db.query(AdhkarCategory).count() > 0:
        return

    categories_data = [
        {
            "name_ar": "أذكار الصباح",
            "name_en": "Morning Adhkar",
            "order": 1,
            "items": [
                {"text_ar": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ", "repetitions": 1, "source": "مسلم"},
                {"text_ar": "اللَّهُمَّ بِكَ أَصْبَحْنَا، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ", "repetitions": 1, "source": "الترمذي"},
                {"text_ar": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ", "repetitions": 100, "source": "مسلم"},
                {"text_ar": "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ", "repetitions": 10, "source": "البخاري"},
                {"text_ar": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ", "repetitions": 3, "source": "مسلم"},
            ],
        },
        {
            "name_ar": "أذكار المساء",
            "name_en": "Evening Adhkar",
            "order": 2,
            "items": [
                {"text_ar": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ", "repetitions": 1, "source": "مسلم"},
                {"text_ar": "اللَّهُمَّ بِكَ أَمْسَيْنَا، وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ الْمَصِيرُ", "repetitions": 1, "source": "الترمذي"},
                {"text_ar": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ", "repetitions": 100, "source": "مسلم"},
                {"text_ar": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ", "repetitions": 3, "source": "مسلم"},
            ],
        },
        {
            "name_ar": "أذكار بعد الصلاة",
            "name_en": "After Prayer",
            "order": 3,
            "items": [
                {"text_ar": "أَسْتَغْفِرُ اللَّهَ", "repetitions": 3, "source": "مسلم"},
                {"text_ar": "اللَّهُمَّ أَنْتَ السَّلَامُ وَمِنْكَ السَّلَامُ، تَبَارَكْتَ يَا ذَا الْجَلَالِ وَالْإِكْرَامِ", "repetitions": 1, "source": "مسلم"},
                {"text_ar": "سُبْحَانَ اللَّهِ", "repetitions": 33, "source": "مسلم"},
                {"text_ar": "الْحَمْدُ لِلَّهِ", "repetitions": 33, "source": "مسلم"},
                {"text_ar": "اللَّهُ أَكْبَرُ", "repetitions": 33, "source": "مسلم"},
                {"text_ar": "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ", "repetitions": 1, "source": "مسلم"},
            ],
        },
        {
            "name_ar": "أذكار النوم",
            "name_en": "Before Sleeping",
            "order": 4,
            "items": [
                {"text_ar": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "repetitions": 1, "source": "البخاري"},
                {"text_ar": "اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ", "repetitions": 3, "source": "أبو داود"},
                {"text_ar": "سُبْحَانَ اللَّهِ", "repetitions": 33, "source": "البخاري"},
                {"text_ar": "الْحَمْدُ لِلَّهِ", "repetitions": 33, "source": "البخاري"},
                {"text_ar": "اللَّهُ أَكْبَرُ", "repetitions": 34, "source": "البخاري"},
            ],
        },
        {
            "name_ar": "أذكار عامة",
            "name_en": "General Adhkar",
            "order": 5,
            "items": [
                {"text_ar": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ", "repetitions": 100, "source": "البخاري"},
                {"text_ar": "لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ", "repetitions": 100, "source": "البخاري"},
                {"text_ar": "اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ", "repetitions": 10, "source": "الترمذي"},
                {"text_ar": "أَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ", "repetitions": 100, "source": "البخاري"},
            ],
        },
    ]

    for cat_data in categories_data:
        cat = AdhkarCategory(
            name_ar=cat_data["name_ar"],
            name_en=cat_data.get("name_en"),
            order=cat_data["order"],
        )
        db.add(cat)
        db.flush()
        for idx, item in enumerate(cat_data["items"]):
            db.add(AdhkarItem(
                category_id=cat.id,
                text_ar=item["text_ar"],
                repetitions=item["repetitions"],
                source=item.get("source"),
                order=idx,
            ))
    db.commit()
    print("[SEED] Adhkar categories and items created")


def seed_settings(db: Session) -> None:
    """Default application settings."""
    defaults = {
        "site_name": "مركز تحفيظ القرآن",
        "center_name": "مركز تحفيظ القرآن الكريم",
        "contact_phone": "",
        "contact_email": "",
        "default_timezone": "Asia/Riyadh",
        "prayer_method": "4",
        "default_city": "Riyadh",
        "default_country": "Saudi Arabia",
    }
    for key, value in defaults.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            db.add(Setting(key=key, value=value))
    db.commit()
    print("[SEED] Settings initialized")


def seed_welcome_announcement(db: Session) -> None:
    if db.query(Announcement).count() > 0:
        return
    db.add(Announcement(
        title="مرحباً بكم في مركز تحفيظ القرآن",
        content="نرحب بجميع الطلاب في نظام إدارة التحفيظ. يمكنكم متابعة تقدمكم، الدرجات، الجداول، والأذكار من خلال لوحة التحكم الخاصة بكم.",
        is_important=True,
        is_published=True,
    ))
    db.commit()
    print("[SEED] Welcome announcement created")


def run_seed(db: Session) -> None:
    """Run all seed functions."""
    seed_admin(db)
    seed_adhkar(db)
    seed_settings(db)
    seed_welcome_announcement(db)
    print("[SEED] Database seeding completed.")
