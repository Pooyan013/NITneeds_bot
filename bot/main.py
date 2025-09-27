import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from threading import Timer
from keys import *
from database import add_or_update_user, get_all_users
import time
from hash import hash
import uuid
import json
import os

bot = telebot.TeleBot(hash)
channel_username = "@nit_needs"  
JOB_ADMIN_ID = 112911597
#___________________________________BUTTONS________________________________________________
buttons = [
    "🏷 فروشی", 
    "❓ درخواستی", 
    "🏡 همخونه",
    "📤ارسال جزوه و فایل",
    "🔍 گمشده", 
    "🔎 پیدا شده",
    "💡فرصت شغلی",
    "📩 اطلاعات اساتید", 
    "📈 تبلیغات", 
    "📞 ارتباط با ادمین", 
]


home_button= [
    "👧همخونه دختر",
    "👦همخونه پسر",
    "🔙 بازگشت"
]
home_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
home_keyboard.add(*home_button)

keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
keyboard_markup.add(*buttons)

faculty = ["علوم پایه", "معارف","مکانیک", "عمران", "شیمی", "صنایع و مواد", "برق و کامپیوتر", "🔙 بازگشت"]
faculty_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
faculty_markup.add(*faculty)

admins = ["درخواستی ها", "ردشده ها"]
admins_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
admins_markup.add(*admins)

back = ["🔙 بازگشت"]
back_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
back_markup.add(*back)

pending_requests = []
user_states = {}


REQUESTS_FILE = "user_requests.json"

if os.path.exists("user_request_limits.json"):
    with open("user_request_limits.json", "r", encoding="utf-8") as f:
        user_request_limits = json.load(f)
else:
    user_request_limits = {}

user_requests_data = {}
LIMIT_PERIOD = 90 * 24 * 60 * 60
MAX_REQUESTS = 10

def save_user_limits():
    with open("user_request_limits.json", "w", encoding="utf-8") as f:
        json.dump(user_request_limits, f, ensure_ascii=False, indent=2)


def save_user_requests():
    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_requests_data, f, ensure_ascii=False, indent=2)

last_request_times = {}
timers = {} 
#____________________________________Verfication FUNCTION________________________________________

def check_channel_membership(user_id):
    try:
        status = bot.get_chat_member(channel_username, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False
    
def timeout_message(chat_id):
    if chat_id in user_states:
        del user_states[chat_id]
        bot.send_message(
            chat_id,
            "⏰ زمان شما برای ارسال درخواست به پایان رسید. دوباره امتحان کنید.",
            reply_markup=keyboard_markup
        )
            
def send_subscription_prompt(chat_id):
    markup = InlineKeyboardMarkup()
    subscribe_button = InlineKeyboardButton("🔗 عضویت در کانال", url="https://t.me/nit_needs")
    check_subscription_button = InlineKeyboardButton("✔️ تایید عضویت", callback_data="check_subscription")
    markup.add(subscribe_button, check_subscription_button)
    bot.send_message(chat_id, "برای استفاده از ربات ابتدا باید عضو کانال شوید.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    chat_id = call.message.chat.id
    if check_channel_membership(chat_id):
        bot.answer_callback_query(call.id, "عضویت شما تایید شد! حالا می‌توانید از ربات استفاده کنید.")
        bot.send_message(chat_id, "به صفحه اصلی بازگشتید.", reply_markup=keyboard_markup)
    else:
        bot.answer_callback_query(call.id, "هنوز عضو کانال نیستید. لطفاً ابتدا عضو شوید.")

#____________________________________HANDLERS_____________________________________________

admin_roles = {
    112911597: "all", 
    442513360: "all",
    244143516: "all",
    101108999: "all",
    1751472873: "all",  
    581500840: "all",
    5410322306: "all",  
    101108994: "all",  
    6695777982: "all",     
}

@bot.message_handler(commands=["admin"])
def admin(message):
    admin_id = message.from_user.id
    admin_role = admin_roles.get(admin_id, None)

    if admin_role is None:
        bot.send_message(message.chat.id, "شما دسترسی لازم برای مشاهده درخواست‌ها را ندارید.")
        return

    if admin_role == "all":
        relevant_requests = pending_requests
    else:
        relevant_requests = [req for req in pending_requests if req["hashtag"] == f"#{admin_role}"]

    if len(relevant_requests) == 0:
        bot.send_message(message.chat.id, "هیچ درخواستی برای تایید وجود ندارد.")
    else:
        for request in relevant_requests:
            markup = InlineKeyboardMarkup()
            accept_button = InlineKeyboardButton("✅ تایید", callback_data=f"accept_{request['request_id']}")
            reject_button = InlineKeyboardButton("❌ رد", callback_data=f"reject_{request['request_id']}")
            markup.add(accept_button, reject_button)

            bot.send_message(
                message.chat.id,
                f"درخواست از {request['user_id']}:\n{request['message']}",
                reply_markup=markup
            )


@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت")
def back_to_main(message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id] 
        
    timer = timers.pop(chat_id, None)
    if timer:
        timer.cancel()

    bot.send_message(chat_id, "به صفحه اصلی بازگشتید.", reply_markup=keyboard_markup)

import time

@bot.message_handler(commands=["broadcast"])
def broadcast_message(message):
    if message.from_user.id in [112911597, 244143516, 101108999]:
        bot.send_message(message.chat.id, "لطفاً پیام خود را (ویدئو، عکس یا متن) برای ارسال به همه کاربران وارد کنید:")
        bot.register_next_step_handler(message, send_broadcast)
    else:
        bot.send_message(message.chat.id, "شما دسترسی لازم برای این کار را ندارید.")

def send_broadcast(message):
    users = get_all_users()
    from_chat_id = message.chat.id
    message_id = message.message_id

    for user in users:
        try:
            bot.copy_message(chat_id=user.user_id, from_chat_id=from_chat_id, message_id=message_id)
            time.sleep(0.1)
        except Exception as e:
            print(f"خطا در ارسال پیام به کاربر {user.user_id}: {e}")
    
    bot.send_message(message.chat.id, "پیام شما با موفقیت به تمام کاربران ارسال شد.")


@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    username = message.from_user.username
    full_name = message.from_user.first_name + " " + (message.from_user.last_name or "")
    
    add_or_update_user(chat_id, username, full_name)
    
    bot.send_message(chat_id, f"""سلام به ربات نیازمندی‌ها خوش اومدی 🩷
چطوری میتونم بهت کمک کنم؟""", reply_markup=keyboard_markup)


def handle_request(message, hashtag, instruction_text):
    chat_id = message.chat.id

    if not check_channel_membership(chat_id):
        send_subscription_prompt(chat_id)
        return

    allowed, count_or_days = can_send_request(chat_id)
    if not allowed:
        bot.send_message(chat_id, f"⛔ محدودیت ارسال درخواست تمام شده. لطفاً بعد از {count_or_days} روز دوباره تلاش کنید.")
        return

    now = time.time()
    if chat_id in last_request_times and now - last_request_times[chat_id] < 100:
        remaining_time = int(100 - (now - last_request_times[chat_id]))
        bot.send_message(chat_id, f"لطفاً {remaining_time} ثانیه صبر کنید تا بتوانید درخواست جدید ارسال کنید.")
        return

    bot.send_message(chat_id, instruction_text, reply_markup=back_markup)

    user_states[chat_id] = {"state": "waiting_for_message", "hashtag": hashtag}

    last_request_times[chat_id] = now

    timer = Timer(120, timeout_message, [chat_id])
    timer.start()
    timers[chat_id] = timer

def update_user_request_count(chat_id):
    now = time.time()
    data = user_request_limits.get(chat_id)

    if not data:
        user_request_limits[chat_id] = {
            "requests_count": MAX_REQUESTS - 1,
            "first_request_time": now
        }
    else:
        elapsed = now - data["first_request_time"]
        if elapsed > LIMIT_PERIOD:
            data["requests_count"] = MAX_REQUESTS - 1
            data["first_request_time"] = now
        else:
            data["requests_count"] -= 1

    save_user_limits()

def get_remaining_requests(chat_id):
    data = user_request_limits.get(chat_id)
    if not data:
        return MAX_REQUESTS
    now = time.time()
    elapsed = now - data["first_request_time"]
    if elapsed > LIMIT_PERIOD:
        return MAX_REQUESTS
    return data["requests_count"]


def notify_admin(request_id):
    request_exists = any(req['request_id'] == request_id for req in pending_requests)
    
    if request_exists:
        for admin_id in admin_roles:
            try:
                bot.send_message(admin_id, "یک درخواست بیش از یک ساعت است که بدون پاسخ باقی مانده است.")
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")


@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id]["state"] == "waiting_for_message")
def process_user_message(message):
    chat_id = int(message.chat.id)  
    user_message = message.text
    state = user_states.get(chat_id)
    if not state:
        return
    hashtag = state["hashtag"]


    user_data = user_requests_data.get(chat_id, {"timestamps": []})
    now = time.time()

    user_data["timestamps"] = [t for t in user_data["timestamps"] if now - t < LIMIT_PERIOD]

    if len(user_data["timestamps"]) >= MAX_REQUESTS:
        remaining_time = int((LIMIT_PERIOD - (now - user_data["timestamps"][0])) / (24*60*60))
        bot.send_message(message.chat.id, f"⛔ محدودیت درخواست‌های شما پر شده است. {remaining_time} روز دیگر دوباره می‌توانید درخواست دهید.")
        return

    if any(r["user_id"] == message.chat.id and not r["approved"] for r in pending_requests):
        bot.send_message(message.chat.id, "⛔ شما قبلاً یک درخواست ارسال کردید که هنوز بررسی نشده.")
        return

    final_message = f"❓{user_message}" if hashtag == "#درخواستی" else f"{hashtag}\n{user_message}"
    request_id = str(uuid.uuid4())

    pending_requests.append({
        "request_id": request_id,
        "user_id": message.chat.id,
        "message": final_message,
        "hashtag": hashtag,
        "approved": False,
        "user_message_id": message.message_id,
        "username": message.from_user.username,
        "full_name": message.from_user.first_name + " " + (message.from_user.last_name or ""),
        "admin_messages": {}
    })

    user_data["timestamps"].append(now)
    user_requests_data[chat_id] = user_data
    save_user_requests()

    remaining_requests = MAX_REQUESTS - len(user_data["timestamps"])
    bot.send_message(message.chat.id, f"✅ درخواست شما ثبت شد. تعداد درخواست‌های باقی‌مانده شما: {remaining_requests}")

    user_states.pop(message.chat.id, None)

    if hashtag == "#فرصت_شغلی":
        target_admins = [JOB_ADMIN_ID]
    else:
        target_admins = admin_roles.keys()

    for admin_id in target_admins:
        try:
            if admin_id in pending_requests[-1]["admin_messages"]:
                continue

            markup = InlineKeyboardMarkup()
            accept_button = InlineKeyboardButton("✅ تایید", callback_data=f"accept_{request_id}")
            reject_button = InlineKeyboardButton("❌ رد", callback_data=f"reject_{request_id}")
            markup.add(accept_button, reject_button)

            sender_info = f"👤 فرستنده: @{message.from_user.username}" if message.from_user.username else f"👤 فرستنده: {message.from_user.first_name} {message.from_user.last_name or ''}"

            sent_msg = bot.send_message(admin_id, f"{sender_info}\n\nدرخواست جدید:\n{final_message}", reply_markup=markup)
            pending_requests[-1]["admin_messages"][admin_id] = sent_msg.message_id

        except Exception as e:
            print(f"خطا در ارسال به ادمین {admin_id}: {e}")


@bot.message_handler()
def main(message):
    chat_id = message.chat.id
    if message.text in ["📤ارسال جزوه و فایل", "📩 اطلاعات اساتید", "📈 تبلیغات", "📞 ارتباط با ادمین"]:
        if check_channel_membership(chat_id):
            if message.text == "📤ارسال جزوه و فایل":
                bot.send_message(chat_id, text_send, reply_markup=back_markup)
            elif message.text == "📩 اطلاعات اساتید":
                bot.send_message(chat_id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟", reply_markup=faculty_markup)
            elif message.text == "📈 تبلیغات":
                bot.send_message(chat_id, text_tablighat)
            elif message.text == "📞 ارتباط با ادمین":
                bot.send_message(chat_id, text_admin)
        else:
            send_subscription_prompt(chat_id)
    
    elif message.text == "❓ درخواستی":
        handle_request(message, "#درخواستی", text_darkhasti)
        
    elif message.text == "🏷 فروشی":
        handle_request(message, "#فروشی", text_foroshi)
    
    elif message.text == "🏡 همخونه":
        bot.send_message(chat_id, "لطفاً انتخاب کنید:", reply_markup=home_keyboard)

    elif message.text == "👧همخونه دختر":
        handle_request(message, "#همخونه_دختر", "لطفاً متن درخواست همخونه دختر خود را وارد کنید:")

    elif message.text == "👦همخونه پسر":
        handle_request(message, "#همخونه_پسر", "لطفاً متن درخواست همخونه پسر خود را وارد کنید:")

    elif message.text == "🔍 گمشده":
        handle_request(message, "#گمشده", text_gomshode)

    elif message.text == "🔎 پیدا شده":
        handle_request(message, "#پیدا_شده", text_peyda_shode)

    elif message.text == "💡فرصت شغلی":
        handle_request(message, "#فرصت_شغلی", text_job)

    elif message.text == "برق و کامپیوتر":
        bot.send_message(message.chat.id, bargh_facility)

    elif message.text == "علوم پایه":
        bot.send_message(message.chat.id, paye_facility)

    elif message.text == "معارف":
        bot.send_message(message.chat.id, maaref_facility)


@bot.message_handler(func=lambda message: message.text == "📩 اطلاعات اساتید")
def handle_faculty_info(message):
    if check_channel_membership(message.chat.id):
        bot.send_message(message.chat.id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟", reply_markup=faculty_markup)
    else:
        send_subscription_prompt(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_admin_action(call):
    action, request_id = call.data.split("_", 1)
    request = next((r for r in pending_requests if r["request_id"] == request_id), None)

    if not request:
        bot.answer_callback_query(call.id, "❗ درخواست پیدا نشد یا قبلاً رسیدگی شده.")
        return

    if request["hashtag"] == "#فرصت_شغلی" and call.from_user.id != JOB_ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ فقط ادمین فرصت شغلی می‌تواند این درخواست را مدیریت کند.")
        return

    chat_id = call.message.chat.id

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)

    if action == "accept":
        bot.send_message(channel_username, f"{request['message']}\n")
        safe_send_message(request["user_id"], "✅ درخواستت تایید شد و در کانال منتشر شد.")
        bot.send_message(chat_id, "✅ درخواست با موفقیت تایید شد.", reply_markup=keyboard_markup)

        for admin_id, msg_id in request["admin_messages"].items():
            try:
                bot.edit_message_reply_markup(chat_id=admin_id, message_id=msg_id, reply_markup=None)
            except Exception as e:
                print(f"خطا در حذف دکمه‌ها از پیام {admin_id}: {e}")

        if request in pending_requests:
            pending_requests.remove(request)


    elif action == "reject":
        bot.answer_callback_query(call.id, "در حال انتظار برای دلیل رد شدن...")
        msg = bot.send_message(chat_id, "❌ لطفاً دلیل رد شدن این درخواست را وارد کنید:")

        user_states[chat_id] = {"state": "waiting_for_rejection_reason", "request_id": request_id}
        for admin_id, msg_id in request["admin_messages"].items():
            try:
                bot.edit_message_reply_markup(chat_id=admin_id, message_id=msg_id, reply_markup=None)
            except Exception as e:
                print(f"خطا در حذف دکمه‌ها از پیام {admin_id}: {e}")

        bot.register_next_step_handler(msg, process_rejection_reason)

def process_rejection_reason(message):
    chat_id = message.chat.id
    state = user_states.pop(chat_id, None)

    if not state:
        bot.send_message(chat_id, "⛔ درخواست نامعتبر یا منقضی شده.")
        return

    request_id = state["request_id"]
    request = next((r for r in pending_requests if r["request_id"] == request_id), None)

    if not request:
        bot.send_message(chat_id, "❗ درخواست پیدا نشد یا قبلاً رسیدگی شده.")
        return

    reason = message.text.strip()
    safe_send_message(request["user_id"], f"❌ درخواستت رد شد.\n📝 دلیل: {reason}")
    bot.send_message(chat_id, "✅ درخواست با موفقیت رد شد.", reply_markup=keyboard_markup)

    if request in pending_requests:
        pending_requests.remove(request)

def can_send_request(chat_id):
    now = time.time()
    data = user_request_limits.get(chat_id)

    if not data:
        user_request_limits[chat_id] = {
            "requests_count": MAX_REQUESTS,
            "first_request_time": now
        }
        save_user_limits()
        return True, MAX_REQUESTS

    elapsed = now - data["first_request_time"]

    if elapsed > LIMIT_PERIOD:
        data["requests_count"] = MAX_REQUESTS
        data["first_request_time"] = now
        save_user_limits()
        return True, MAX_REQUESTS

    if data["requests_count"] <= 0:
        remaining_days = int((LIMIT_PERIOD - elapsed) / (24*60*60))
        return False, remaining_days

    return True, data["requests_count"]


def safe_send_message(chat_id, text, **kwargs):
    try:
        bot.send_message(chat_id, text, **kwargs)
    except telebot.apihelper.ApiTelegramException as e:
        if "Forbidden: bot was blocked by the user" in str(e):
            print(f"❌ کاربر {chat_id} ربات رو بلاک کرده.")
        else:
            print(f"⚠️ خطا در ارسال پیام به {chat_id}: {e}")

bot.infinity_polling()
