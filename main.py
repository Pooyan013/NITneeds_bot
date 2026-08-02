import logging

from bot.db import init_db
from bot.logging_setup import configure_logging
from bot.services.rate_limit import load_cache

configure_logging()
init_db()
load_cache()

from bot.handlers import admin, menu, requests, start, subscription  
from bot.bot_instance import bot  

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Bot starting...")
    bot.infinity_polling()
