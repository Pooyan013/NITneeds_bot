import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Timer

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.bot_instance import bot
from bot.config import ADMIN_IDS, JOB_ADMIN_ID, REQUEST_COOLDOWN_SECONDS, REQUEST_TIMEOUT_SECONDS
from bot.handlers.subscription import is_channel_member, send_subscription_prompt
from bot.keyboards import back_menu, main_menu
from bot.content.texts import BACK_BUTTON
from bot.services import rate_limit
from bot.state import last_request_times, pending_requests, timers, user_states

logger = logging.getLogger(__name__)

_notification_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="admin-notify",
)

_LIMIT_EXPLANATION = (
    "💡محدودیت پیام‌های درخواستی فقط و فقط جهت جلوگیری از ترافیک پیام‌ها و ترغیب شما به "
    "جستجو در کانال قبل از ارسال درخواستی می‌باشد (بسیاری از درخواستی‌ها تکراری بوده و با "
    "یک جستجوی ساده پیدا خواهند شد).\n\nسپاس از همکاری شما❤️"
)


def timed_send_message(chat_id, text, *, operation: str, **kwargs):
    """Send a Telegram message and record the network duration in the logs."""
    started_at = time.perf_counter()
    try:
        return bot.send_message(chat_id, text, **kwargs)
    finally:
        logger.info(
            "Telegram send operation=%s chat_id=%s duration=%.3fs",
            operation,
            chat_id,
            time.perf_counter() - started_at,
        )


def safe_send_message(chat_id, text, **kwargs) -> None:
    try:
        timed_send_message(chat_id, text, operation="safe_send_message", **kwargs)
    except Exception:
        logger.exception("Failed to send message to %s", chat_id)


def _notify_admins(request: dict, target_admins: list[int], sender_info: str) -> None:
    """Notify each target admin independently so one failed chat does not block others."""
    request_id = request["request_id"]
    for admin_id in target_admins:
        started_at = time.perf_counter()
        try:
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("\u2705 \u062a\u0627\u06cc\u06cc\u062f", callback_data=f"accept_{request_id}"),
                InlineKeyboardButton("\u274c \u0631\u062f", callback_data=f"reject_{request_id}"),
            )
            sent_msg = timed_send_message(
                admin_id,
                f"{sender_info}\n\n\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u062c\u062f\u06cc\u062f:\n{request['message']}",
                operation=f"admin_notification:{request_id}",
                reply_markup=markup,
            )
            request["admin_messages"][admin_id] = sent_msg.message_id
            logger.info(
                "Admin notification delivered request_id=%s admin_id=%s duration=%.3fs",
                request_id,
                admin_id,
                time.perf_counter() - started_at,
            )
        except Exception:
            logger.exception(
                "Failed to notify admin %s about request %s",
                admin_id,
                request_id,
            )


def build_request(message, hashtag: str) -> dict:
    """Build the in-memory request record from a Telegram text message."""
    user_message = message.text.strip()
    final_message = f"❓{user_message}" if hashtag == "#درخواستی" else f"{hashtag}\n{user_message}"
    return {
        "request_id": str(uuid.uuid4()),
        "user_id": message.chat.id,
        "message": final_message,
        "hashtag": hashtag,
        "approved": False,
        "user_message_id": message.message_id,
        "username": message.from_user.username,
        "full_name": f"{message.from_user.first_name} {message.from_user.last_name or ''}",
        "admin_messages": {},
    }


def _timeout_message(chat_id: int) -> None:
    if chat_id in user_states:
        del user_states[chat_id]
        bot.send_message(
            chat_id,
            "⏰ زمان شما برای ارسال درخواست به پایان رسید. دوباره امتحان کنید.",
            reply_markup=main_menu,
        )


def handle_request(message, hashtag: str, instruction_text: str) -> None:
    chat_id = message.chat.id

    if chat_id in ADMIN_IDS:
        bot.send_message(chat_id, "✅ شما به عنوان ادمین می‌توانید بدون محدودیت درخواست ارسال کنید.")
        bot.send_message(chat_id, instruction_text, reply_markup=back_menu)
        user_states[chat_id] = {"state": "waiting_for_message", "hashtag": hashtag}
        return

    if not is_channel_member(chat_id):
        send_subscription_prompt(chat_id)
        return

    allowed, count_or_days = rate_limit.can_send_request(chat_id)
    if not allowed:
        bot.send_message(
            chat_id, f"⛔ محدودیت ارسال درخواست تمام شده. لطفاً بعد از {count_or_days} روز دوباره تلاش کنید."
        )
        return

    now = time.time()
    last = last_request_times.get(chat_id)
    if last and now - last < REQUEST_COOLDOWN_SECONDS:
        remaining_time = int(REQUEST_COOLDOWN_SECONDS - (now - last))
        bot.send_message(chat_id, f"لطفاً {remaining_time} ثانیه صبر کنید تا بتوانید درخواست جدید ارسال کنید.")
        return

    bot.send_message(chat_id, instruction_text, reply_markup=back_menu)
    user_states[chat_id] = {"state": "waiting_for_message", "hashtag": hashtag}
    last_request_times[chat_id] = now

    old_timer = timers.pop(chat_id, None)
    if old_timer:
        old_timer.cancel()

    timer = Timer(REQUEST_TIMEOUT_SECONDS, _timeout_message, [chat_id])
    timer.start()
    timers[chat_id] = timer


@bot.message_handler(
    func=lambda message: message.chat.id in user_states
    and user_states[message.chat.id]["state"] == "waiting_for_message"
    and message.text != BACK_BUTTON
)
def process_user_message(message):
    started_at = time.perf_counter()
    chat_id = int(message.chat.id)

    if not message.text or not message.text.strip():
        bot.send_message(chat_id, "لطفاً متن درخواست را ارسال کنید.", reply_markup=back_menu)
        return

    if chat_id not in ADMIN_IDS:
        rate_limit_started_at = time.perf_counter()
        allowed, count_or_days = rate_limit.can_send_request(chat_id)
        logger.info(
            "Rate-limit check user_id=%s duration=%.3fs",
            chat_id,
            time.perf_counter() - rate_limit_started_at,
        )
        if not allowed:
            bot.send_message(
                chat_id,
                f"⛔ 📌تعداد درخواستی‌های شما به پایان رسیده‌است.\n"
                f"تا شارژ مجدد پیام‌های شما:{count_or_days} روز\n\n{_LIMIT_EXPLANATION}",
            )
            user_states.pop(chat_id, None)
            timer = timers.pop(chat_id, None)
            if timer:
                timer.cancel()
            return

    state = user_states.get(chat_id)
    if not state:
        return
    hashtag = state["hashtag"]

    if any(r["user_id"] == chat_id and not r["approved"] for r in pending_requests):
        bot.send_message(chat_id, "⛔ شما قبلاً یک درخواست ارسال کردید که هنوز بررسی نشده.")
        return

    request = build_request(message, hashtag)
    pending_requests.append(request)
    request_id = request["request_id"]

    if chat_id not in ADMIN_IDS:
        persist_started_at = time.perf_counter()
        rate_limit.register_request(chat_id)
        logger.info(
            "Rate-limit persistence user_id=%s duration=%.3fs",
            chat_id,
            time.perf_counter() - persist_started_at,
        )
        remaining = rate_limit.remaining_requests(chat_id)
        timed_send_message(
            chat_id,
            f"✅ درخواست شما ثبت شد و پس از تایید در کانال قرار خواهد گرفت.\n"
            f"تعداد درخواست‌های باقی‌مانده شما: {remaining}\n\n{_LIMIT_EXPLANATION}",
            operation="request_confirmation",
        )

    user_states.pop(chat_id, None)
    timer = timers.pop(chat_id, None)
    if timer:
        timer.cancel()

    target_admins = [JOB_ADMIN_ID] if hashtag == "#فرصت_شغلی" else list(ADMIN_IDS)
    sender_info = (
        f"👤 فرستنده: @{message.from_user.username}"
        if message.from_user.username
        else f"👤 فرستنده: {message.from_user.first_name} {message.from_user.last_name or ''}"
    )

    _notification_executor.submit(_notify_admins, request, target_admins, sender_info)
    logger.info(
        "Admin notifications queued request_id=%s admins=%d",
        request_id,
        len(target_admins),
    )
    logger.info(
        "Total request processing request_id=%s user_id=%s duration=%.3fs",
        request_id,
        chat_id,
        time.perf_counter() - started_at,
    )
