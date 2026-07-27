import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from threading import Timer
from keys import *
from hash import hash
import uuid
import os
import time
from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified

engine = create_engine('sqlite:///users.db', echo=False, connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    full_name = Column(String)
    usage_count = Column(Integer, default=0)
    request_limit = relationship("RequestLimit", back_populates="user", uselist=False)

class RequestLimit(Base):
    __tablename__ = 'request_limits'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True)
    timestamps = Column(JSON, default=list)
    user = relationship("User", back_populates="request_limit")

Base.metadata.create_all(engine)

bot = telebot.TeleBot(hash)
channel_username = "@nit_needs"  
JOB_ADMIN_ID = 112911597

LIMIT_PERIOD = 90 * 24 * 60 * 60  
MAX_REQUESTS = 10

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
last_request_times = {}
timers = {}
user_requests_data = {} 

def load_user_requests():
    global user_requests_data
    with Session() as session:
        limits = session.query(RequestLimit).all()
        user_requests_data = {limit.user_id: {"timestamps": limit.timestamps or []} for limit in limits}

load_user_requests()

def add_or_update_user(user_id, username, full_name):
    with Session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.username = username
            user.full_name = full_name
            user.usage_count += 1
        else:
            user = User(user_id=user_id, username=username, full_name=full_name, usage_count=1)
            session.add(user)
        session.commit()

def get_all_users():
    with Session() as session:
        return session.query(User).all()

def save_user_requests():
    with Session() as session:
        for chat_id, data in user_requests_data.items():
            limit = session.query(RequestLimit).filter_by(user_id=chat_id).first()
            new_ts = list(data.get("timestamps", []))
            if not limit:
                limit = RequestLimit(user_id=chat_id, timestamps=new_ts)
                session.add(limit)
            else:
                limit.timestamps = new_ts
                flag_modified(limit, "timestamps")
        session.commit()

def can_send_request_db(user_id):
    now = time.time()
    user_data = user_requests_data.get(user_id, {"timestamps": []})
    user_data["timestamps"] = [t for t in user_data["timestamps"] if now - t < LIMIT_PERIOD]
    user_requests_data[user_id] = user_data

    if len(user_data["timestamps"]) >= MAX_REQUESTS:
        remaining_days = int((LIMIT_PERIOD - (now - user_data["timestamps"][0])) / (24*60*60))
        return False, remaining_days

    return True, MAX_REQUESTS - len(user_data["timestamps"])

def register_request(user_id):
    now = time.time()
    user_data = user_requests_data.get(user_id, {"timestamps": []})
    user_data["timestamps"].append(now)
    user_requests_data[user_id] = user_data
    save_user_requests()

def remove_limit(user_id):
    with Session() as session:
        limit = session.query(RequestLimit).filter_by(user_id=user_id).first()
        if limit:
            session.delete(limit)
            session.commit()
    if user_id in user_requests_data:
        user_requests_data[user_id]["timestamps"] = []

def check_channel_membership(user_id):
    try:
        status = bot.get_chat_member(channel_username, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
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
        except Exception:
            pass
    
    bot.send_message(message.chat.id, "پیام شما با موفقیت به تمام کاربران ارسال شد.")


@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    username = message.from_user.username
    full_name = message.from_user.first_name + " " + (message.from_user.last_name or "")
    
    add_or_update_user(chat_id, username, full_name)
    
    bot.send_message(chat_id, "سلام به ربات نیازمندی‌ها خوش اومدی 🩷\nچطوری میتونم بهت کمک کنم؟", reply_markup=keyboard_markup)


def handle_request(message, hashtag, instruction_text):
    chat_id = message.chat.id

    if chat_id in admin_roles:
        bot.send_message(chat_id, "✅ شما به عنوان ادمین می‌توانید بدون محدودیت درخواست ارسال کنید.")
        bot.send_message(chat_id, instruction_text, reply_markup=back_markup)
        user_states[chat_id] = {"state": "waiting_for_message", "hashtag": hashtag}
        return

    if not check_channel_membership(chat_id):
        send_subscription_prompt(chat_id)
        return
    
    allowed, count_or_days = can_send_request_db(chat_id)
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

    if chat_id in timers:
        timers[chat_id].cancel()
        del timers[chat_id]

    timer = Timer(120, timeout_message, [chat_id])
    timer.start()
    timers[chat_id] = timer


@bot.message_handler(commands=['unlimit'])
def unlimit_user(message):
    if message.chat.id not in admin_roles:
        bot.reply_to(message, "⛔ شما اجازه انجام این کار را ندارید.")
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "⚙️ لطفاً به‌صورت صحیح وارد کنید:\n/unlimit [user_id]")
        return

    target_id = int(parts[1])
    remove_limit(target_id)
    bot.reply_to(message, f"✅ محدودیت کاربر با شناسه {target_id} با موفقیت حذف شد.")


def safe_send_message(chat_id, text, **kwargs):
    try:
        bot.send_message(chat_id, text, **kwargs)
    except telebot.apihelper.ApiTelegramException:
        pass


@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id]["state"] == "waiting_for_message")
def process_user_message(message):
    chat_id = int(message.chat.id)

    if chat_id not in admin_roles:
        user_data = user_requests_data.get(chat_id, {"timestamps": []})
        now = time.time()
        user_data["timestamps"] = [t for t in user_data["timestamps"] if now - t < LIMIT_PERIOD]

        if len(user_data["timestamps"]) >= MAX_REQUESTS:
            remaining_time = int((LIMIT_PERIOD - (now - user_data["timestamps"][0])) / (24*60*60))
            bot.send_message(chat_id, 
                f"⛔ 📌تعداد درخواستی‌های شما به پایان رسیده‌است.\n"
                f"تا شارژ مجدد پیام‌های شما:{remaining_time} روز\n\n"
                f"💡محدودیت پیام‌های درخواستی فقط و فقط جهت جلوگیری از ترافیک پیام‌ها و ترغیب شما به جستجو در کانال قبل از ارسال درخواستی می‌باشد(بسیاری از درخواستی‌ها تکراری بوده و با یک جستجوی ساده پیدا خواهند شد).\n\n"
                f"سپاس از همکاری شما❤️"
            )
            user_states.pop(chat_id, None)
            if chat_id in timers:
                timers[chat_id].cancel()
                del timers[chat_id]
            return

    user_message = message.text
    state = user_states.get(chat_id)
    if not state:
        return
    hashtag = state["hashtag"]

    if any(r["user_id"] == chat_id and not r["approved"] for r in pending_requests):
        bot.send_message(chat_id, "⛔ شما قبلاً یک درخواست ارسال کردید که هنوز بررسی نشده.")
        return

    final_message = f"❓{user_message}" if hashtag == "#درخواستی" else f"{hashtag}\n{user_message}"
    request_id = str(uuid.uuid4())

    pending_requests.append({
        "request_id": request_id,
        "user_id": chat_id,
        "message": final_message,
        "hashtag": hashtag,
        "approved": False,
        "user_message_id": message.message_id,
        "username": message.from_user.username,
        "full_name": message.from_user.first_name + " " + (message.from_user.last_name or ""),
        "admin_messages": {}
    })

    if chat_id not in admin_roles:
        register_request(chat_id)
        remaining_requests = MAX_REQUESTS - len(user_requests_data[chat_id]["timestamps"])
        bot.send_message(chat_id, 
            f"✅ درخواست شما ثبت شد و پس از تایید در کانال قرار خواهد گرفت.\n"
            f"تعداد درخواست‌های باقی‌مانده شما: {remaining_requests}\n\n"
            f"💡محدودیت پیام‌های درخواستی فقط و فقط جهت جلوگیری از ترافیک پیام‌ها و ترغیب شما به جستجو در کانال قبل از ارسال درخواستی می‌باشد (بسیاری از درخواستی‌ها تکراری بوده و با یک جستجوی ساده پیدا خواهند شد).\n\n"
            f"سپاس از همکاری شما❤️"
        )

    user_states.pop(chat_id, None)
    if chat_id in timers:
        timers[chat_id].cancel()
        del timers[chat_id]

    if hashtag == "#فرصت_شغلی":
        target_admins = [JOB_ADMIN_ID]
    else:
        target_admins = admin_roles.keys()

    sender_info = f"👤 فرستنده: @{message.from_user.username}" if message.from_user.username else f"👤 فرستنده: {message.from_user.first_name} {message.from_user.last_name or ''}"

    for admin_id in target_admins:
        try:
            markup = InlineKeyboardMarkup()
            accept_button = InlineKeyboardButton("✅ تایید", callback_data=f"accept_{request_id}")
            reject_button = InlineKeyboardButton("❌ رد", callback_data=f"reject_{request_id}")
            markup.add(accept_button, reject_button)

            sent_msg = bot.send_message(admin_id, f"{sender_info}\n\nدرخواست جدید:\n{final_message}", reply_markup=markup)
            pending_requests[-1]["admin_messages"][admin_id] = sent_msg.message_id
        except Exception:
            pass


@bot.message_handler()
def main(message):
    chat_id = message.chat.id
    if message.text in ["📤ارسال جزوه و فایل", "📩 اطلاعات اساتید", "📈 تبلیغات", "📞 ارتباط با ادمین"]:
        if check_channel_membership(chat_id):
            if message.text == "📤ارسال جزوه و فایل":
                try: bot.send_message(chat_id, text_send, reply_markup=back_markup)
                except NameError: bot.send_message(chat_id, "متن ارسال فایل یافت نشد.", reply_markup=back_markup)
            elif message.text == "📩 اطلاعات اساتید":
                bot.send_message(chat_id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟", reply_markup=faculty_markup)
            elif message.text == "📈 تبلیغات":
                try: bot.send_message(chat_id, text_tablighat)
                except NameError: pass
            elif message.text == "📞 ارتباط با ادمین":
                try: bot.send_message(chat_id, text_admin)
                except NameError: pass
        else:
            send_subscription_prompt(chat_id)
    
    elif message.text == "❓ درخواستی":
        try: handle_request(message, "#درخواستی", text_darkhasti)
        except NameError: handle_request(message, "#درخواستی", "متن درخواست خود را بنویسید:")
        
    elif message.text == "🏷 فروشی":
        try: handle_request(message, "#فروشی", text_foroshi)
        except NameError: handle_request(message, "#فروشی", "متن فروش خود را بنویسید:")
    
    elif message.text == "🏡 همخونه":
        bot.send_message(chat_id, "لطفاً انتخاب کنید:", reply_markup=home_keyboard)

    elif message.text == "👧همخونه دختر":
        handle_request(message, "#همخونه_دختر", "لطفاً متن درخواست همخونه دختر خود را وارد کنید:")

    elif message.text == "👦همخونه پسر":
        handle_request(message, "#همخونه_پسر", "لطفاً متن درخواست همخونه پسر خود را وارد کنید:")

    elif message.text == "🔍 گمشده":
        try: handle_request(message, "#گمشده", text_gomshode)
        except NameError: handle_request(message, "#گمشده", "مشخصات گمشده را بنویسید:")

    elif message.text == "🔎 پیدا شده":
        try: handle_request(message, "#پیدا_شده", text_peyda_shode)
        except NameError: handle_request(message, "#پیدا_شده", "مشخصات پیدا شده را بنویسید:")

    elif message.text == "💡فرصت شغلی":
        try: handle_request(message, "#فرصت_شغلی", text_job)
        except NameError: handle_request(message, "#فرصت_شغلی", "فرصت شغلی را بنویسید:")

    elif message.text == "برق و کامپیوتر":
        try: bot.send_message(message.chat.id, bargh_facility)
        except NameError: pass

    elif message.text == "علوم پایه":
        try: bot.send_message(message.chat.id, paye_facility)
        except NameError: pass

    elif message.text == "معارف":
        try: bot.send_message(message.chat.id, maaref_facility)
        except NameError: pass


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

    if action == "accept":
        for admin_chat_id, msg_id in request["admin_messages"].items():
            try:
                admin_username = (
                    f"@{call.from_user.username}"
                    if call.from_user.username
                    else str(call.from_user.id)
                )

                user_username = (
                    f"@{request['username']}"
                    if request["username"]
                    else str(request["user_id"])
                )

                text = (
                    "✅ تایید شد توسط ادمین\n\n"
                    f"👮 ادمین: {admin_username}\n"
                    f"👤 کاربر: {user_username}\n\n"
                    f"{request['message']}"
                )

                bot.edit_message_text(
                    text=text,
                    chat_id=admin_chat_id,
                    message_id=msg_id,
                    reply_markup=None
                )

            except Exception:
                pass     

                
        bot.send_message(channel_username, f"{request['message']}\n")
        safe_send_message(request["user_id"], "✅ درخواستت تایید شد و در کانال منتشر شد.")
        bot.send_message(chat_id, "✅ درخواست با موفقیت تایید شد.", reply_markup=keyboard_markup)
        
        if request in pending_requests:
            pending_requests.remove(request)

    elif action == "reject":
        bot.answer_callback_query(call.id, "در حال انتظار برای دلیل رد شدن...")
        msg = bot.send_message(chat_id, "❌ لطفاً دلیل رد شدن این درخواست را وارد کنید:")
        user_states[chat_id] = {"state": "waiting_for_rejection_reason", "request_id": request_id}
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
    
    for admin_chat_id, msg_id in request["admin_messages"].items():
        try:
            admin_username = (
                f"@{message.from_user.username}"
                if message.from_user.username
                else str(message.from_user.id)
            )

            user_username = (
                f"@{request['username']}"
                if request["username"]
                else str(request["user_id"])
            )

            text = (
                "❌ رد شد توسط ادمین\n\n"
                f"👮 ادمین: {admin_username}\n"
                f"👤 کاربر: {user_username}\n"
                f"📝 دلیل: {reason}\n\n"
                f"{request['message']}"
            )

            bot.edit_message_text(
                text=text,
                chat_id=admin_chat_id,
                message_id=msg_id,
                reply_markup=None
            )

        except Exception:
            pass
    if request in pending_requests:
        pending_requests.remove(request)

if __name__ == '__main__':
    bot.infinity_polling()