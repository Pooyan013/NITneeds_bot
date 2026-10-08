import logging

from bot.db import init_db
from bot.logging_setup import configure_logging
from bot.services.rate_limit import load_cache

configure_logging()
init_db()
load_cache()

# Import handlers in an intentional order. `menu` has a catch-all text handler,
# so command and stateful handlers must be registered before it can consume them.
from bot.handlers import start, subscription, menu, admin, requests
from bot.bot_instance import bot  

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Bot starting...")
    bot.infinity_polling()
