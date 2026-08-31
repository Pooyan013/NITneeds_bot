# NIT Needs Bot

![NIT Needs Bot](docs/bot-preview.png)

NIT Needs is a Telegram bot built for the student community of Babol Noshirvani University of Technology.

It helps students share and find everyday needs in one place: items for sale, lost and found posts, roommate requests, job opportunities, questions, and more.

The bot has been running in production for nearly two years and is used by real students on a daily basis. This repository contains the refactored and cleaned-up version of the project, prepared as a portfolio piece.

## Demo

Here is a short video showing the main user flow, from joining the channel and submitting a request to admin review and publication:

<a href="YOUR_DEMO_VIDEO_URL">
  <img src="docs/bot-preview.png" alt="Watch the NIT Needs Bot demo" width="720">
</a>

## What the bot does

- Lets users submit posts through a simple button-based menu
- Sends submitted posts to admins for review
- Allows admins to approve or reject posts
- Sends rejection feedback back to the original user
- Publishes approved posts to the public Telegram channel
- Requires channel membership for selected features
- Applies per-user request limits and a cooldown between submissions
- Provides a faculty contact directory
- Supports admin broadcasts with text, photos, and videos

## Request flow

```text
User selects a category
          ↓
Bot collects the request
          ↓
Admins review the request
       ↙       ↘
   Rejected    Approved
      ↓           ↓
 User gets    Published in
 feedback     the channel
```

## Tech stack

- Python 3.11+
- pyTelegramBotAPI
- SQLAlchemy
- SQLite
- python-dotenv
- Docker and Docker Compose

## Project structure

```text
main.py                         # Application entry point
bot/
├── config.py                   # Environment-based configuration
├── bot_instance.py             # Shared Telegram bot instance
├── db.py                       # Database setup
├── models.py                   # SQLAlchemy models
├── state.py                    # Runtime conversation state
├── keyboards.py                # Telegram keyboards
├── content/                    # Bot messages and contact data
├── services/
│   ├── users.py                # User persistence
│   └── rate_limit.py           # Request limit handling
└── handlers/
    ├── start.py                # /start command
    ├── menu.py                 # Main menu routing
    ├── requests.py             # Request submission flow
    ├── subscription.py         # Channel membership checks
    └── admin.py                # Admin actions and broadcasts
tests/                          # Unit tests
Dockerfile
docker-compose.yml
```

## Running locally

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
python main.py
```

On Windows, use `copy .env.example .env` instead of `cp`.

Set the required values in `.env` before starting the bot.

## Running with Docker

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f bot
```

On Windows, use `copy .env.example .env` instead of `cp`.

The SQLite database is stored in `./data/users.db`, so it survives container recreation.

## Configuration

| Variable                   | Description                                              | Default              |
| -------------------------- | -------------------------------------------------------- | -------------------- |
| `BOT_TOKEN`                | Telegram bot token from BotFather                        | Required             |
| `CHANNEL_USERNAME`         | Public channel used for membership checks and publishing | `@nit_needs`         |
| `DATABASE_URL`             | SQLAlchemy database URL                                  | `sqlite:///users.db` |
| `JOB_ADMIN_ID`             | Admin responsible for job-post approvals                 | `0`                  |
| `ADMIN_IDS`                | Comma-separated Telegram IDs of regular admins           | Empty                |
| `BROADCAST_ADMIN_IDS`      | Admin IDs allowed to use `/broadcast`                    | Same as `ADMIN_IDS`  |
| `RATE_LIMIT_PERIOD_DAYS`   | Length of the rolling request-limit window               | `90`                 |
| `MAX_REQUESTS`             | Maximum requests per user in the window                  | `10`                 |
| `REQUEST_COOLDOWN_SECONDS` | Minimum time between submissions                         | `100`                |
| `REQUEST_TIMEOUT_SECONDS`  | Time allowed for completing a request                    | `120`                |

## Admin commands

- `/admin` — view pending requests
- `/unlimit <user_id>` — remove a user's request limit
- `/broadcast` — send a message to registered users

## Tests

Install the development dependencies and run the test suite:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

The tests run locally and do not send requests to the Telegram API.

## Contact data

The real faculty contact data is kept outside version control. A sample file is included as `bot/content/faculty_contacts.example.py`.

## Security

The public bot username and demo media are safe to include in this repository. Before publishing screenshots or videos, make sure they do not reveal:

- `BOT_TOKEN` or the contents of `.env`
- Private admin IDs or internal configuration
- Real phone numbers or email addresses that should remain private
- Usernames, messages, or other personal information without permission

The bot token should only exist in `.env` or in the deployment environment and must never be committed to Git.

## License

MIT
