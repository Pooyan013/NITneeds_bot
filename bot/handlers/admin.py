import logging
import time

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.bot_instance import bot
from bot.config import ADMIN_IDS, BROADCAST_ADMIN_IDS, CHANNEL_USERNAME, JOB_ADMIN_ID
from bot.handlers.requests import safe_send_message
from bot.keyboards import main_menu
from bot.services.rate_limit import remove_limit
from bot.services.users import get_all_users
from bot.state import pending_requests, user_states

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "شما دسترسی لازم برای مشاهده درخواست‌ها را ندارید.")
        return

    if not pending_requests:
        bot.send_message(message.chat.id, "هیچ درخواستی برای تایید وجود ندارد.")
        return

    for request in pending_requests:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ تایید", callback_data=f"accept_{request['request_id']}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{request['request_id']}"),
        )
        bot.send_message(
            message.chat.id, f"درخواست از {request['user_id']}:\n{request['message']}", reply_markup=markup
        )


@bot.message_handler(commands=["unlimit"])
def unlimit_user(message):
    if message.chat.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔ شما اجازه انجام این کار را ندارید.")
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "⚙️ لطفاً به‌صورت صحیح وارد کنید:\n/unlimit [user_id]")
        return

    target_id = int(parts[1])
    remove_limit(target_id)
    bot.reply_to(message, f"✅ محدودیت کاربر با شناسه {target_id} با موفقیت حذف شد.")


@bot.message_handler(commands=["broadcast"])
def broadcast_message(message):
    if message.from_user.id in BROADCAST_ADMIN_IDS:
        bot.send_message(message.chat.id, "لطفاً پیام خود را (ویدئو، عکس یا متن) برای ارسال به همه کاربران وارد کنید:")
        bot.register_next_step_handler(message, _send_broadcast)
    else:
        bot.send_message(message.chat.id, "شما دسترسی لازم برای این کار را ندارید.")


def _send_broadcast(message):
    users = get_all_users()
    sent, failed = 0, 0
    for user in users:
        try:
            bot.copy_message(chat_id=user.user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            sent += 1
            time.sleep(0.1)
        except Exception:
            failed += 1
            logger.warning("Broadcast delivery failed for user %s", user.user_id)

    bot.send_message(message.chat.id, f"پیام شما ارسال شد. ({sent} موفق، {failed} ناموفق)")


def _admin_display_name(user) -> str:
    return f"@{user.username}" if user.username else str(user.id)


def _requester_display_name(request: dict) -> str:
    return f"@{request['username']}" if request["username"] else str(request["user_id"])


def _can_manage_request(user_id: int, request: dict) -> bool:
    if request["hashtag"] == "#فرصت_شغلی":
        return user_id == JOB_ADMIN_ID
    return user_id in ADMIN_IDS


@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_admin_action(call):
    action, request_id = call.data.split("_", 1)
    request = next((r for r in pending_requests if r["request_id"] == request_id), None)

    if request and not _can_manage_request(call.from_user.id, request):
        bot.answer_callback_query(call.id, "⛔ فقط ادمین مجاز می‌تواند این درخواست را مدیریت کند.")
        return

    if request and request["approved"]:
        bot.answer_callback_query(call.id, "این درخواست قبلاً تأیید شده است.")
        return

    if call.from_user.id not in ADMIN_IDS and call.from_user.id != JOB_ADMIN_ID:
        bot.answer_callback_query(call.id, "شما دسترسی مدیریت درخواست‌ها را ندارید.", show_alert=True)
        return

    if not request:
        bot.answer_callback_query(call.id, "❗ درخواست پیدا نشد یا قبلاً رسیدگی شده.")
        return

    if request["hashtag"] == "#فرصت_شغلی" and call.from_user.id != JOB_ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ فقط ادمین فرصت شغلی می‌تواند این درخواست را مدیریت کند.")
        return

    chat_id = call.message.chat.id

    if action == "accept":
        _approve_request(request, call.from_user, chat_id)
    else:
        bot.answer_callback_query(call.id, "در حال انتظار برای دلیل رد شدن...")
        msg = bot.send_message(chat_id, "❌ لطفاً دلیل رد شدن این درخواست را وارد کنید:")
        user_states[chat_id] = {"state": "waiting_for_rejection_reason", "request_id": request_id}
        bot.register_next_step_handler(msg, _process_rejection_reason)


def _approve_request(request: dict, admin_user, chat_id: int) -> None:
    if request["approved"]:
        return
    request["approved"] = True

    for admin_chat_id, msg_id in request["admin_messages"].items():
        try:
            text = (
                "✅ تایید شد توسط ادمین\n\n"
                f"👮 ادمین: {_admin_display_name(admin_user)}\n"
                f"👤 کاربر: {_requester_display_name(request)}\n\n"
                f"{request['message']}"
            )
            bot.edit_message_text(text=text, chat_id=admin_chat_id, message_id=msg_id, reply_markup=None)
        except Exception:
            logger.exception("Failed to update admin message %s", msg_id)

    try:
        bot.send_message(CHANNEL_USERNAME, f"{request['message']}\n")
    except Exception:
        request["approved"] = False
        logger.exception("Failed to publish request %s", request["request_id"])
        bot.send_message(chat_id, "❌ انتشار درخواست در کانال ناموفق بود؛ لطفاً دوباره تلاش کنید.")
        return
    safe_send_message(request["user_id"], "✅ درخواستت تایید شد و در کانال منتشر شد.")
    bot.send_message(chat_id, "✅ درخواست با موفقیت تایید شد.", reply_markup=main_menu)

    if request in pending_requests:
        pending_requests.remove(request)


def _process_rejection_reason(message):
    chat_id = message.chat.id
    state = user_states.pop(chat_id, None)

    if not state:
        bot.send_message(chat_id, "⛔ درخواست نامعتبر یا منقضی شده.")
        return

    request = next((r for r in pending_requests if r["request_id"] == state["request_id"]), None)
    if not request:
        bot.send_message(chat_id, "❗ درخواست پیدا نشد یا قبلاً رسیدگی شده.")
        return

    if not message.text or not message.text.strip():
        bot.send_message(chat_id, "لطفاً دلیل رد را به‌صورت متنی ارسال کنید.")
        user_states[chat_id] = state
        return

    reason = message.text.strip()
    safe_send_message(request["user_id"], f"❌ درخواستت رد شد.\n📝 دلیل: {reason}")
    bot.send_message(chat_id, "✅ درخواست با موفقیت رد شد.", reply_markup=main_menu)

    for admin_chat_id, msg_id in request["admin_messages"].items():
        try:
            text = (
                "❌ رد شد توسط ادمین\n\n"
                f"👮 ادمین: {_admin_display_name(message.from_user)}\n"
                f"👤 کاربر: {_requester_display_name(request)}\n"
                f"📝 دلیل: {reason}\n\n"
                f"{request['message']}"
            )
            bot.edit_message_text(text=text, chat_id=admin_chat_id, message_id=msg_id, reply_markup=None)
        except Exception:
            logger.exception("Failed to update admin message %s", msg_id)

    if request in pending_requests:
        pending_requests.remove(request)
