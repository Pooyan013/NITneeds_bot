# NIT Needs Bot 🎓

A Telegram bot that runs the "needs/requests" board for a university's student
community — for-sale posts, lost & found, roommate search, job postings, and
paid channel ads — with a human-in-the-loop admin approval workflow before
anything is published to the public channel.

**Live in production for 1.5+ years**, handling real student traffic. This
repository is a refactor of that production codebase into a cleaner,
portfolio-ready architecture — same behavior, better structure.

## Features

- 📋 **Structured submission flow** — students pick a category (for sale,
  request, lost item, found item, job posting, roommate search), the bot
  collects the text, and it's queued for admin review.
- ✅ **Admin approval queue** — every submission is sent to admins with
  inline _Approve_ / _Reject_ buttons. Rejections ask for a reason, which
  is relayed back to the user.
- 🔒 **Channel-membership gate** — several features only unlock once the
  user has joined the public channel; the bot checks membership via the
  Telegram API and prompts to subscribe otherwise.
- ⏳ **Per-user rate limiting** — configurable max requests per rolling
  time window, backed by the database so it survives restarts, plus a
  short cooldown between consecutive submissions.
- 📢 **Broadcast command** — a restricted set of admins can push a message
  (text, photo, or video) to every user who has ever started the bot.
- 🏫 **Static info lookup** — faculty contact directory served by
  department, and channel-advertising rates.

## Architecture

The original code was a single ~600-line `main.py` with duplicated
SQLAlchemy models, hardcoded secrets, and Telegram-API calls mixed
directly into business logic. It worked, but it wasn't something you'd
want to hand to another developer — or put in a portfolio.

This refactor splits it into layers, without changing the underlying
stack (still pyTelegramBotAPI + SQLAlchemy — a full framework migration
wasn't worth it for a bot this size):

```
nit-needs-bot/
├── main.py                      # entry point: init DB, load cache, register handlers, poll
├── bot/
│   ├── config.py                 # all settings read from environment (.env)
│   ├── bot_instance.py           # single shared telebot.TeleBot instance
│   ├── db.py                     # SQLAlchemy engine/session/Base
│   ├── models.py                 # User, RequestLimit (single source of truth)
│   ├── state.py                  # in-memory runtime state (pending requests, FSM, timers)
│   ├── keyboards.py               # ReplyKeyboardMarkup definitions
│   ├── logging_setup.py
│   ├── content/
│   │   ├── texts.py               # static bot copy (no secrets/PII)
│   │   ├── faculty_contacts.py    # real contact data — gitignored
│   │   └── faculty_contacts.example.py  # placeholder, safe to commit
│   ├── services/
│   │   ├── users.py               # user CRUD
│   │   └── rate_limit.py          # request-limit cache + persistence
│   └── handlers/
│       ├── start.py               # /start
│       ├── subscription.py        # channel-membership check + prompt
│       ├── menu.py                # main text-button router
│       ├── requests.py            # submission flow + FSM state handler
│       └── admin.py               # /admin, /unlimit, /broadcast, approve/reject
```

**Why this split:**

- `config.py` — no more secrets hardcoded in source files. Everything
  comes from environment variables, validated at startup.
- `models.py` / `db.py` — the original had the _same_ `User` and
  `RequestLimit` classes defined twice (once in `main.py`, once in
  `database.py`), against two different `Base` instances. That's a bug
  waiting to happen. Now there's exactly one definition.
- `services/` — database and rate-limiting logic no longer needs a
  `bot` object or knowledge of Telegram at all, so it's independently
  testable.
- `handlers/` — each file owns one conversational area instead of one
  600-line function with a long `if/elif` chain.
- `content/` — separates _what the bot says_ from _how it behaves_, and
  keeps real personal data (professors' phone numbers/emails) out of
  version control via `faculty_contacts.example.py`.

### What changed behaviorally (bug fixes, not just reorganizing)

- **Rate-limit persistence bug fixed**: the original `save_user_requests()`
  re-wrote _every_ cached user's timestamps to the database on every
  single new request — O(n) database writes for one action. It now only
  persists the user who just made a request.
- **Dead `try/except NameError` blocks removed**: the original guarded
  every text-sending call with `except NameError` because `keys.py`
  might not define a given variable if `from keys import *` partially
  failed. Since `content/texts.py` is now a real, always-imported
  module, that defensive (and silent-failure-prone) pattern is gone.
- **Exceptions are now logged**, not silently swallowed — every bare
  `except: pass` in the original either logs via `logger.exception`
  or does something visible.

### Known limitations carried over from the original

- Four faculty buttons (مکانیک, عمران, شیمی, صنایع و مواد) exist in the
  menu but have no handler — same gap as the original, left as-is
  rather than inventing content that isn't mine to write.
- `pending_requests` and FSM state (`user_states`) live in memory, not
  in the database. Fine for a single-process bot; would need to move to
  Redis or the DB before running multiple workers.
- SQLite is the default; swap `DATABASE_URL` for Postgres in production
  if you expect concurrent writers.

## Tech stack

- Python 3.11+
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- SQLAlchemy (ORM)
- python-dotenv (config)

## Setup

```bash
git clone <this-repo>
cd nit-needs-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in BOT_TOKEN, ADMIN_IDS, CHANNEL_USERNAME, etc.

cp bot/content/faculty_contacts.example.py bot/content/faculty_contacts.py
# fill in real contact data if you need that feature

python main.py
```

### Environment variables

| Variable                   | Required | Default              | Description                                                     |
| -------------------------- | -------- | -------------------- | --------------------------------------------------------------- |
| `BOT_TOKEN`                | ✅       | —                    | Token from [@BotFather](https://t.me/BotFather)                 |
| `CHANNEL_USERNAME`         |          | `@nit_needs`         | Public channel the bot posts approved content to                |
| `DATABASE_URL`             |          | `sqlite:///users.db` | Any SQLAlchemy-compatible URL                                   |
| `JOB_ADMIN_ID`             |          | `0`                  | Telegram user ID that manages job-posting approvals             |
| `ADMIN_IDS`                |          | _(empty)_            | Comma-separated admin user IDs                                  |
| `BROADCAST_ADMIN_IDS`      |          | same as `ADMIN_IDS`  | Subset allowed to run `/broadcast`                              |
| `RATE_LIMIT_PERIOD_DAYS`   |          | `90`                 | Rolling window for the request limit                            |
| `MAX_REQUESTS`             |          | `10`                 | Max requests per user per window                                |
| `REQUEST_COOLDOWN_SECONDS` |          | `100`                | Minimum gap between two submissions                             |
| `REQUEST_TIMEOUT_SECONDS`  |          | `120`                | How long the bot waits for the submission text before giving up |

## Security note

The original code shipped a live bot token and real personal contact
data (phone numbers, emails) directly in source files. Both are excluded
here: secrets go through `.env` (gitignored), and
`bot/content/faculty_contacts.py` — which holds real personal data — is
gitignored with a placeholder `.example.py` version committed instead.

## License

MIT — do whatever you want with it.
