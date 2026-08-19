"""
Quran reader – uses alquran.cloud API (reliable, legal source).
"""
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from app.security import get_current_user
from app.models import User

router = APIRouter(prefix="/api/quran", tags=["Quran"])

QURAN_API = "https://api.alquran.cloud/v1"

# Surah metadata (static, well-known)
SURAHS = [
    {"number": 1, "name": "الفاتحة", "englishName": "Al-Faatiha", "ayahs": 7, "revelationType": "Meccan"},
    {"number": 2, "name": "البقرة", "englishName": "Al-Baqara", "ayahs": 286, "revelationType": "Medinan"},
    {"number": 3, "name": "آل عمران", "englishName": "Aal-i-Imraan", "ayahs": 200, "revelationType": "Medinan"},
    {"number": 4, "name": "النساء", "englishName": "An-Nisaa", "ayahs": 176, "revelationType": "Medinan"},
    {"number": 5, "name": "المائدة", "englishName": "Al-Maaida", "ayahs": 120, "revelationType": "Medinan"},
    {"number": 6, "name": "الأنعام", "englishName": "Al-An'aam", "ayahs": 165, "revelationType": "Meccan"},
    {"number": 7, "name": "الأعراف", "englishName": "Al-A'raaf", "ayahs": 206, "revelationType": "Meccan"},
    {"number": 8, "name": "الأنفال", "englishName": "Al-Anfaal", "ayahs": 75, "revelationType": "Medinan"},
    {"number": 9, "name": "التوبة", "englishName": "At-Tawba", "ayahs": 129, "revelationType": "Medinan"},
    {"number": 10, "name": "يونس", "englishName": "Yunus", "ayahs": 109, "revelationType": "Meccan"},
    {"number": 11, "name": "هود", "englishName": "Hud", "ayahs": 123, "revelationType": "Meccan"},
    {"number": 12, "name": "يوسف", "englishName": "Yusuf", "ayahs": 111, "revelationType": "Meccan"},
    {"number": 13, "name": "الرعد", "englishName": "Ar-Ra'd", "ayahs": 43, "revelationType": "Medinan"},
    {"number": 14, "name": "إبراهيم", "englishName": "Ibrahim", "ayahs": 52, "revelationType": "Meccan"},
    {"number": 15, "name": "الحجر", "englishName": "Al-Hijr", "ayahs": 99, "revelationType": "Meccan"},
    {"number": 16, "name": "النحل", "englishName": "An-Nahl", "ayahs": 128, "revelationType": "Meccan"},
    {"number": 17, "name": "الإسراء", "englishName": "Al-Israa", "ayahs": 111, "revelationType": "Meccan"},
    {"number": 18, "name": "الكهف", "englishName": "Al-Kahf", "ayahs": 110, "revelationType": "Meccan"},
    {"number": 19, "name": "مريم", "englishName": "Maryam", "ayahs": 98, "revelationType": "Meccan"},
    {"number": 20, "name": "طه", "englishName": "Taa-Haa", "ayahs": 135, "revelationType": "Meccan"},
    {"number": 21, "name": "الأنبياء", "englishName": "Al-Anbiyaa", "ayahs": 112, "revelationType": "Meccan"},
    {"number": 22, "name": "الحج", "englishName": "Al-Hajj", "ayahs": 78, "revelationType": "Medinan"},
    {"number": 23, "name": "المؤمنون", "englishName": "Al-Muminoon", "ayahs": 118, "revelationType": "Meccan"},
    {"number": 24, "name": "النور", "englishName": "An-Noor", "ayahs": 64, "revelationType": "Medinan"},
    {"number": 25, "name": "الفرقان", "englishName": "Al-Furqaan", "ayahs": 77, "revelationType": "Meccan"},
    {"number": 26, "name": "الشعراء", "englishName": "Ash-Shu'araa", "ayahs": 227, "revelationType": "Meccan"},
    {"number": 27, "name": "النمل", "englishName": "An-Naml", "ayahs": 93, "revelationType": "Meccan"},
    {"number": 28, "name": "القصص", "englishName": "Al-Qasas", "ayahs": 88, "revelationType": "Meccan"},
    {"number": 29, "name": "العنكبوت", "englishName": "Al-Ankaboot", "ayahs": 69, "revelationType": "Meccan"},
    {"number": 30, "name": "الروم", "englishName": "Ar-Room", "ayahs": 60, "revelationType": "Meccan"},
    {"number": 31, "name": "لقمان", "englishName": "Luqman", "ayahs": 34, "revelationType": "Meccan"},
    {"number": 32, "name": "السجدة", "englishName": "As-Sajda", "ayahs": 30, "revelationType": "Meccan"},
    {"number": 33, "name": "الأحزاب", "englishName": "Al-Ahzaab", "ayahs": 73, "revelationType": "Medinan"},
    {"number": 34, "name": "سبأ", "englishName": "Saba", "ayahs": 54, "revelationType": "Meccan"},
    {"number": 35, "name": "فاطر", "englishName": "Faatir", "ayahs": 45, "revelationType": "Meccan"},
    {"number": 36, "name": "يس", "englishName": "Yaseen", "ayahs": 83, "revelationType": "Meccan"},
    {"number": 37, "name": "الصافات", "englishName": "As-Saaffaat", "ayahs": 182, "revelationType": "Meccan"},
    {"number": 38, "name": "ص", "englishName": "Saad", "ayahs": 88, "revelationType": "Meccan"},
    {"number": 39, "name": "الزمر", "englishName": "Az-Zumar", "ayahs": 75, "revelationType": "Meccan"},
    {"number": 40, "name": "غافر", "englishName": "Ghafir", "ayahs": 85, "revelationType": "Meccan"},
    {"number": 41, "name": "فصلت", "englishName": "Fussilat", "ayahs": 54, "revelationType": "Meccan"},
    {"number": 42, "name": "الشورى", "englishName": "Ash-Shura", "ayahs": 53, "revelationType": "Meccan"},
    {"number": 43, "name": "الزخرف", "englishName": "Az-Zukhruf", "ayahs": 89, "revelationType": "Meccan"},
    {"number": 44, "name": "الدخان", "englishName": "Ad-Dukhaan", "ayahs": 59, "revelationType": "Meccan"},
    {"number": 45, "name": "الجاثية", "englishName": "Al-Jaathiya", "ayahs": 37, "revelationType": "Meccan"},
    {"number": 46, "name": "الأحقاف", "englishName": "Al-Ahqaf", "ayahs": 35, "revelationType": "Meccan"},
    {"number": 47, "name": "محمد", "englishName": "Muhammad", "ayahs": 38, "revelationType": "Medinan"},
    {"number": 48, "name": "الفتح", "englishName": "Al-Fath", "ayahs": 29, "revelationType": "Medinan"},
    {"number": 49, "name": "الحجرات", "englishName": "Al-Hujuraat", "ayahs": 18, "revelationType": "Medinan"},
    {"number": 50, "name": "ق", "englishName": "Qaaf", "ayahs": 45, "revelationType": "Meccan"},
    {"number": 51, "name": "الذاريات", "englishName": "Adh-Dhaariyat", "ayahs": 60, "revelationType": "Meccan"},
    {"number": 52, "name": "الطور", "englishName": "At-Tur", "ayahs": 49, "revelationType": "Meccan"},
    {"number": 53, "name": "النجم", "englishName": "An-Najm", "ayahs": 62, "revelationType": "Meccan"},
    {"number": 54, "name": "القمر", "englishName": "Al-Qamar", "ayahs": 55, "revelationType": "Meccan"},
    {"number": 55, "name": "الرحمن", "englishName": "Ar-Rahmaan", "ayahs": 78, "revelationType": "Medinan"},
    {"number": 56, "name": "الواقعة", "englishName": "Al-Waaqia", "ayahs": 96, "revelationType": "Meccan"},
    {"number": 57, "name": "الحديد", "englishName": "Al-Hadid", "ayahs": 29, "revelationType": "Medinan"},
    {"number": 58, "name": "المجادلة", "englishName": "Al-Mujaadila", "ayahs": 22, "revelationType": "Medinan"},
    {"number": 59, "name": "الحشر", "englishName": "Al-Hashr", "ayahs": 24, "revelationType": "Medinan"},
    {"number": 60, "name": "الممتحنة", "englishName": "Al-Mumtahana", "ayahs": 13, "revelationType": "Medinan"},
    {"number": 61, "name": "الصف", "englishName": "As-Saff", "ayahs": 14, "revelationType": "Medinan"},
    {"number": 62, "name": "الجمعة", "englishName": "Al-Jumu'a", "ayahs": 11, "revelationType": "Medinan"},
    {"number": 63, "name": "المنافقون", "englishName": "Al-Munaafiqoon", "ayahs": 11, "revelationType": "Medinan"},
    {"number": 64, "name": "التغابن", "englishName": "At-Taghaabun", "ayahs": 18, "revelationType": "Medinan"},
    {"number": 65, "name": "الطلاق", "englishName": "At-Talaaq", "ayahs": 12, "revelationType": "Medinan"},
    {"number": 66, "name": "التحريم", "englishName": "At-Tahrim", "ayahs": 12, "revelationType": "Medinan"},
    {"number": 67, "name": "الملك", "englishName": "Al-Mulk", "ayahs": 30, "revelationType": "Meccan"},
    {"number": 68, "name": "القلم", "englishName": "Al-Qalam", "ayahs": 52, "revelationType": "Meccan"},
    {"number": 69, "name": "الحاقة", "englishName": "Al-Haaqqa", "ayahs": 52, "revelationType": "Meccan"},
    {"number": 70, "name": "المعارج", "englishName": "Al-Ma'aarij", "ayahs": 44, "revelationType": "Meccan"},
    {"number": 71, "name": "نوح", "englishName": "Nooh", "ayahs": 28, "revelationType": "Meccan"},
    {"number": 72, "name": "الجن", "englishName": "Al-Jinn", "ayahs": 28, "revelationType": "Meccan"},
    {"number": 73, "name": "المزمل", "englishName": "Al-Muzzammil", "ayahs": 20, "revelationType": "Meccan"},
    {"number": 74, "name": "المدثر", "englishName": "Al-Muddaththir", "ayahs": 56, "revelationType": "Meccan"},
    {"number": 75, "name": "القيامة", "englishName": "Al-Qiyaama", "ayahs": 40, "revelationType": "Meccan"},
    {"number": 76, "name": "الإنسان", "englishName": "Al-Insaan", "ayahs": 31, "revelationType": "Medinan"},
    {"number": 77, "name": "المرسلات", "englishName": "Al-Mursalaat", "ayahs": 50, "revelationType": "Meccan"},
    {"number": 78, "name": "النبأ", "englishName": "An-Naba", "ayahs": 40, "revelationType": "Meccan"},
    {"number": 79, "name": "النازعات", "englishName": "An-Naazi'aat", "ayahs": 46, "revelationType": "Meccan"},
    {"number": 80, "name": "عبس", "englishName": "Abasa", "ayahs": 42, "revelationType": "Meccan"},
    {"number": 81, "name": "التكوير", "englishName": "At-Takwir", "ayahs": 29, "revelationType": "Meccan"},
    {"number": 82, "name": "الانفطار", "englishName": "Al-Infitaar", "ayahs": 19, "revelationType": "Meccan"},
    {"number": 83, "name": "المطففين", "englishName": "Al-Mutaffifin", "ayahs": 36, "revelationType": "Meccan"},
    {"number": 84, "name": "الانشقاق", "englishName": "Al-Inshiqaaq", "ayahs": 25, "revelationType": "Meccan"},
    {"number": 85, "name": "البروج", "englishName": "Al-Burooj", "ayahs": 22, "revelationType": "Meccan"},
    {"number": 86, "name": "الطارق", "englishName": "At-Taariq", "ayahs": 17, "revelationType": "Meccan"},
    {"number": 87, "name": "الأعلى", "englishName": "Al-A'laa", "ayahs": 19, "revelationType": "Meccan"},
    {"number": 88, "name": "الغاشية", "englishName": "Al-Ghaashiya", "ayahs": 26, "revelationType": "Meccan"},
    {"number": 89, "name": "الفجر", "englishName": "Al-Fajr", "ayahs": 30, "revelationType": "Meccan"},
    {"number": 90, "name": "البلد", "englishName": "Al-Balad", "ayahs": 20, "revelationType": "Meccan"},
    {"number": 91, "name": "الشمس", "englishName": "Ash-Shams", "ayahs": 15, "revelationType": "Meccan"},
    {"number": 92, "name": "الليل", "englishName": "Al-Lail", "ayahs": 21, "revelationType": "Meccan"},
    {"number": 93, "name": "الضحى", "englishName": "Ad-Dhuhaa", "ayahs": 11, "revelationType": "Meccan"},
    {"number": 94, "name": "الشرح", "englishName": "Ash-Sharh", "ayahs": 8, "revelationType": "Meccan"},
    {"number": 95, "name": "التين", "englishName": "At-Tin", "ayahs": 8, "revelationType": "Meccan"},
    {"number": 96, "name": "العلق", "englishName": "Al-Alaq", "ayahs": 19, "revelationType": "Meccan"},
    {"number": 97, "name": "القدر", "englishName": "Al-Qadr", "ayahs": 5, "revelationType": "Meccan"},
    {"number": 98, "name": "البينة", "englishName": "Al-Bayyina", "ayahs": 8, "revelationType": "Medinan"},
    {"number": 99, "name": "الزلزلة", "englishName": "Az-Zalzala", "ayahs": 8, "revelationType": "Medinan"},
    {"number": 100, "name": "العاديات", "englishName": "Al-Aadiyaat", "ayahs": 11, "revelationType": "Meccan"},
    {"number": 101, "name": "القارعة", "englishName": "Al-Qaari'a", "ayahs": 11, "revelationType": "Meccan"},
    {"number": 102, "name": "التكاثر", "englishName": "At-Takaathur", "ayahs": 8, "revelationType": "Meccan"},
    {"number": 103, "name": "العصر", "englishName": "Al-Asr", "ayahs": 3, "revelationType": "Meccan"},
    {"number": 104, "name": "الهمزة", "englishName": "Al-Humaza", "ayahs": 9, "revelationType": "Meccan"},
    {"number": 105, "name": "الفيل", "englishName": "Al-Fil", "ayahs": 5, "revelationType": "Meccan"},
    {"number": 106, "name": "قريش", "englishName": "Quraish", "ayahs": 4, "revelationType": "Meccan"},
    {"number": 107, "name": "الماعون", "englishName": "Al-Maa'un", "ayahs": 7, "revelationType": "Meccan"},
    {"number": 108, "name": "الكوثر", "englishName": "Al-Kawthar", "ayahs": 3, "revelationType": "Meccan"},
    {"number": 109, "name": "الكافرون", "englishName": "Al-Kaafiroon", "ayahs": 6, "revelationType": "Meccan"},
    {"number": 110, "name": "النصر", "englishName": "An-Nasr", "ayahs": 3, "revelationType": "Medinan"},
    {"number": 111, "name": "المسد", "englishName": "Al-Masad", "ayahs": 5, "revelationType": "Meccan"},
    {"number": 112, "name": "الإخلاص", "englishName": "Al-Ikhlaas", "ayahs": 4, "revelationType": "Meccan"},
    {"number": 113, "name": "الفلق", "englishName": "Al-Falaq", "ayahs": 5, "revelationType": "Meccan"},
    {"number": 114, "name": "الناس", "englishName": "An-Naas", "ayahs": 6, "revelationType": "Meccan"},
]


@router.get("/surahs")
async def list_surahs(
    q: Optional[str] = Query(None),
    current: User = Depends(get_current_user),
):
    """List all 114 surahs with optional search."""
    results = SURAHS
    if q:
        q_lower = q.strip().lower()
        results = [
            s for s in SURAHS
            if q_lower in s["name"] or q_lower in s["englishName"].lower() or q_lower == str(s["number"])
        ]
    return results


@router.get("/surah/{surah_number}")
async def get_surah(
    surah_number: int,
    edition: str = Query("ar.asad"),  # Arabic text
    current: User = Depends(get_current_user),
):
    """Fetch full surah text from alquran.cloud."""
    if surah_number < 1 or surah_number > 114:
        raise HTTPException(status_code=400, detail="رقم السورة غير صالح")

    meta = next((s for s in SURAHS if s["number"] == surah_number), None)

    try:
        # Use quran-uthmani for authentic Arabic text
        url = f"{QURAN_API}/surah/{surah_number}/quran-uthmani"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 200:
                raise HTTPException(status_code=502, detail="فشل جلب نص القرآن")
            surah_data = data["data"]
            ayahs = [
                {
                    "number": a["numberInSurah"],
                    "number_in_quran": a["number"],
                    "text": a["text"],
                    "juz": a.get("juz"),
                    "page": a.get("page"),
                }
                for a in surah_data.get("ayahs", [])
            ]
            return {
                "number": surah_number,
                "name": meta["name"] if meta else surah_data.get("name"),
                "englishName": meta["englishName"] if meta else surah_data.get("englishName"),
                "ayahs_count": len(ayahs),
                "revelationType": meta["revelationType"] if meta else None,
                "ayahs": ayahs,
            }
    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="تعذر الاتصال بخدمة القرآن. حاول لاحقاً.",
        )


@router.get("/juz/{juz_number}")
async def get_juz(
    juz_number: int,
    current: User = Depends(get_current_user),
):
    """Fetch a full Juz."""
    if juz_number < 1 or juz_number > 30:
        raise HTTPException(status_code=400, detail="رقم الجزء غير صالح")
    try:
        url = f"{QURAN_API}/juz/{juz_number}/quran-uthmani"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 200:
                raise HTTPException(status_code=502, detail="فشل جلب الجزء")
            ayahs = [
                {
                    "number": a["number"],
                    "surah": a["surah"]["number"],
                    "surah_name": a["surah"]["name"],
                    "number_in_surah": a["numberInSurah"],
                    "text": a["text"],
                    "page": a.get("page"),
                }
                for a in data["data"].get("ayahs", [])
            ]
            return {"juz": juz_number, "ayahs_count": len(ayahs), "ayahs": ayahs}
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="تعذر الاتصال بخدمة القرآن")
