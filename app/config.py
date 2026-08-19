"""
Application configuration.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database – use /tmp to avoid sandbox disk I/O issues
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/quran_center.db")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "quran-center-secret-key-change-in-production-303121-very-long-and-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# App Settings
APP_NAME = "مركز تحفيظ القرآن"
APP_NAME_EN = "Quran Memorization Center"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Admin seed credentials (will be hashed on first run)
ADMIN_USERNAME = "admin@303121"
ADMIN_PASSWORD = "303121"
ADMIN_FULL_NAME = "مدير النظام"

# Prayer times API
PRAYER_API_BASE = "https://api.aladhan.com/v1"
DEFAULT_PRAYER_METHOD = 4  # Umm Al-Qura University, Makkah
DEFAULT_CITY = "Riyadh"
DEFAULT_COUNTRY = "Saudi Arabia"
