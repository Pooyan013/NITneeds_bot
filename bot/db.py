import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from bot.config import DATABASE_URL

logger = logging.getLogger(__name__)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=_connect_args)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Import models so they register on Base, then create tables."""
    from bot import models  

    Base.metadata.create_all(engine)
    logger.info("Database ready (%s)", DATABASE_URL)
