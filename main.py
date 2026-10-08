import logging
import time

from requests.exceptions import RequestException
from telebot.apihelper import ApiTelegramException

from bot.db import init_db
from bot.logging_setup import configure_logging
from bot.services.rate_limit import load_cache
from bot.config import POLLING_RETRY_DELAY_SECONDS

configure_logging()
init_db()
load_cache()

# Import handlers in an intentional order. `menu` has a catch-all text handler,
# so command and stateful handlers must be registered before it can consume them.
from bot.handlers import start, subscription, menu, admin, requests
from bot.bot_instance import bot  

logger = logging.getLogger(__name__)

def run_polling() -> None:
    """Keep polling alive across transient Telegram/network failures."""
    while True:
        try:
            bot.infinity_polling()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except (RequestException, ApiTelegramException):
            logger.exception(
                "Polling network/API error; retrying in %s seconds",
                POLLING_RETRY_DELAY_SECONDS,
            )
            time.sleep(POLLING_RETRY_DELAY_SECONDS)


if __name__ == "__main__":
    logger.info("Bot starting...")
    run_polling()
