import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"متغیر محیطی {name} تنظیم نشده. فایل .env.example رو کپی کن به .env و مقداردهی کن."
        )
    return value

def _int_set(raw: str) -> set[int]:
    return {int(x) for x in raw.split(",") if x.strip()}

BOT_TOKEN = _require("BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@nit_needs")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///users.db")

JOB_ADMIN_ID = int(os.environ.get("JOB_ADMIN_ID", "0"))
ADMIN_IDS = _int_set(os.environ.get("ADMIN_IDS", ""))

BROADCAST_ADMIN_IDS = _int_set(os.environ.get("BROADCAST_ADMIN_IDS", "")) or ADMIN_IDS

RATE_LIMIT_PERIOD_DAYS = int(os.environ.get("RATE_LIMIT_PERIOD_DAYS", "90"))
RATE_LIMIT_PERIOD = RATE_LIMIT_PERIOD_DAYS * 24 * 60 * 60
MAX_REQUESTS = int(os.environ.get("MAX_REQUESTS", "10"))

REQUEST_COOLDOWN_SECONDS = int(os.environ.get("REQUEST_COOLDOWN_SECONDS", "100"))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "120"))
