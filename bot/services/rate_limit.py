import logging
import time
from typing import Dict, Tuple

from bot.config import MAX_REQUESTS, RATE_LIMIT_PERIOD
from bot.db import Session
from bot.models import RequestLimit

logger = logging.getLogger(__name__)

_cache: Dict[int, dict] = {}


def load_cache() -> None:
    global _cache
    with Session() as session:
        limits = session.query(RequestLimit).all()
        _cache = {limit.user_id: {"timestamps": limit.timestamps or []} for limit in limits}
    logger.info("Rate-limit cache loaded for %d users", len(_cache))


def _persist(user_id: int, timestamps: list) -> None:
    with Session() as session:
        limit = session.query(RequestLimit).filter_by(user_id=user_id).first()
        if not limit:
            limit = RequestLimit(user_id=user_id, timestamps=timestamps)
            session.add(limit)
        else:
            limit.timestamps = timestamps
        session.commit()


def can_send_request(user_id: int) -> Tuple[bool, int]:
    now = time.time()
    data = _cache.setdefault(user_id, {"timestamps": []})
    data["timestamps"] = [t for t in data["timestamps"] if now - t < RATE_LIMIT_PERIOD]

    if len(data["timestamps"]) >= MAX_REQUESTS:
        remaining_days = int((RATE_LIMIT_PERIOD - (now - data["timestamps"][0])) / (24 * 60 * 60))
        return False, remaining_days

    return True, MAX_REQUESTS - len(data["timestamps"])


def register_request(user_id: int) -> None:
    now = time.time()
    data = _cache.setdefault(user_id, {"timestamps": []})
    data["timestamps"].append(now)
    _persist(user_id, data["timestamps"])  


def remaining_requests(user_id: int) -> int:
    data = _cache.get(user_id, {"timestamps": []})
    return MAX_REQUESTS - len(data["timestamps"])


def remove_limit(user_id: int) -> None:
    with Session() as session:
        limit = session.query(RequestLimit).filter_by(user_id=user_id).first()
        if limit:
            session.delete(limit)
            session.commit()
    if user_id in _cache:
        _cache[user_id]["timestamps"] = []
