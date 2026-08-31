# NIT Needs Bot

ربات تلگرامی نیازمندی‌های دانشجویان دانشگاه صنعتی نوشیروانی بابل؛ شامل ثبت آگهی فروش، درخواست، گمشده و پیدا‌شده، هم‌خانه و فرصت شغلی، با تأیید ادمین پیش از انتشار در کانال.

## امکانات

- ثبت درخواست متنی و ارسال آن برای صف بررسی ادمین
- تأیید یا رد درخواست با امکان ارسال دلیل رد به کاربر
- الزام عضویت در کانال برای امکانات مشخص
- محدودیت تعداد درخواست در بازه‌ی زمانی و فاصله‌ی زمانی بین درخواست‌ها
- ارسال broadcast متنی، تصویری یا ویدیویی برای کاربران ثبت‌شده
- نمایش اطلاعات گروه‌های آموزشی
- اجرای محلی یا Docker Compose

## نیازمندی‌ها

- Python 3.11 یا بالاتر
- یک Bot Token از BotFather
- دسترسی ادمین ربات به کانال مقصد برای انتشار درخواست‌ها
- دسترسی ربات به اطلاعات عضویت کانال برای بررسی عضویت کاربران

## اجرای محلی

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env        # در Linux/macOS: cp .env.example .env
python main.py
```

فایل `.env` را با مقادیر واقعی تکمیل کنید. این فایل نباید commit شود.

## اجرای Docker

```bash
copy .env.example .env        # در Linux/macOS: cp .env.example .env
docker compose up -d --build
docker compose logs -f bot
```

دیتابیس SQLite در مسیر `./data/users.db` روی میزبان ذخیره می‌شود و با recreate شدن کانتینر باقی می‌ماند.

برای توقف:

```bash
docker compose down
```

## تنظیمات محیطی

| متغیر | اجباری | مقدار پیش‌فرض | توضیح |
|---|---:|---|---|
| `BOT_TOKEN` | بله | - | توکن ربات |
| `CHANNEL_USERNAME` | خیر | `@nit_needs` | کانال مقصد |
| `DATABASE_URL` | خیر | `sqlite:///users.db` | آدرس SQLAlchemy؛ Compose آن را به `/app/data/users.db` تنظیم می‌کند |
| `JOB_ADMIN_ID` | خیر | `0` | شناسه ادمین بررسی فرصت‌های شغلی |
| `ADMIN_IDS` | خیر | خالی | شناسه ادمین‌ها با جداکننده‌ی کاما |
| `BROADCAST_ADMIN_IDS` | خیر | مقدار `ADMIN_IDS` | ادمین‌های مجاز برای `/broadcast` |
| `RATE_LIMIT_PERIOD_DAYS` | خیر | `90` | طول بازه‌ی محدودیت |
| `MAX_REQUESTS` | خیر | `10` | حداکثر درخواست در بازه |
| `REQUEST_COOLDOWN_SECONDS` | خیر | `100` | فاصله‌ی حداقلی بین دو درخواست |
| `REQUEST_TIMEOUT_SECONDS` | خیر | `120` | زمان انتظار برای متن درخواست |

## اطلاعات تماس دانشکده‌ها

فایل خصوصی `bot/content/faculty_contacts.py` در گیت commit نمی‌شود. در صورت نیاز، آن را از روی `faculty_contacts.example.py` بسازید و اطلاعات واقعی را وارد کنید. اگر فایل خصوصی وجود نداشته باشد، ربات از placeholder عمومی استفاده می‌کند.

## دستورات ادمین

- `/admin` نمایش درخواست‌های در انتظار بررسی
- `/unlimit <user_id>` حذف محدودیت درخواست یک کاربر
- `/broadcast` ارسال پیام به کاربران ثبت‌شده

## تست‌ها

وابستگی‌های توسعه را نصب و تست‌ها را اجرا کنید:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

تست‌ها به Telegram API وصل نمی‌شوند و منطق rate limit و ساخت رکورد درخواست را بررسی می‌کنند.

## ساختار پروژه

```text
main.py
bot/
  config.py
  db.py
  models.py
  state.py
  content/
  services/
  handlers/
tests/
Dockerfile
docker-compose.yml
```

## محدودیت‌های فعلی

- صف درخواست‌ها و state مکالمه در حافظه نگه‌داری می‌شوند و با restart از بین می‌روند.
- اجرای چند worker هم‌زمان بدون انتقال state به Redis یا دیتابیس توصیه نمی‌شود.
- چهار گزینه‌ی دانشکده (`مکانیک`، `عمران`، `شیمی` و `صنایع و مواد`) هنوز محتوای اختصاصی ندارند.
- برای بار هم‌زمان بالا، استفاده از PostgreSQL به‌جای SQLite مناسب‌تر است.
