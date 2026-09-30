import logging
import time
from threading import Lock

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.bot_instance import bot
from bot.config import CHANNEL_USERNAME, MEMBERSHIP_CACHE_TTL_SECONDS
from bot.keyboards import main_menu

logger = logging.getLogger(__name__)

_membership_cache: dict[int, tuple[bool, float]] = {}
_membership_cache_lock = Lock()


def clear_membership_cache(user_id: int | None = None) -> None:
    with _membership_cache_lock:
        if user_id is None:
            _membership_cache.clear()
        else:
            _membership_cache.pop(user_id, None)


def is_channel_member(user_id: int) -> bool:
    now = time.monotonic()
    with _membership_cache_lock:
        cached = _membership_cache.get(user_id)
        if cached and now - cached[1] < MEMBERSHIP_CACHE_TTL_SECONDS:
            logger.debug("Membership cache hit for user %s", user_id)
            return cached[0]
        if cached:
            _membership_cache.pop(user_id, None)

    started_at = time.perf_counter()
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        is_member = status in ("member", "administrator", "creator")
    except Exception:
        logger.exception("Failed to check channel membership for %s", user_id)
        is_member = False

    elapsed = time.perf_counter() - started_at
    with _membership_cache_lock:
        _membership_cache[user_id] = (is_member, time.monotonic())
    logger.info(
        "Membership API check user_id=%s member=%s duration=%.3fs",
        user_id,
        is_member,
        elapsed,
    )
    return is_member


def send_subscription_prompt(chat_id: int) -> None:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔗 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
        InlineKeyboardButton("✔️ تایید عضویت", callback_data="check_subscription"),
    )
    bot.send_message(chat_id, "برای استفاده از ربات ابتدا باید عضو کانال شوید.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    chat_id = call.message.chat.id
    clear_membership_cache(chat_id)
    if is_channel_member(chat_id):
        bot.answer_callback_query(call.id, "عضویت شما تایید شد! حالا می‌توانید از ربات استفاده کنید.")
        bot.send_message(chat_id, "به صفحه اصلی بازگشتید.", reply_markup=main_menu)
    else:
        bot.answer_callback_query(call.id, "هنوز عضو کانال نیستید. لطفاً ابتدا عضو شوید.")
