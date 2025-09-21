import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from threading import Timer
from keys import *
from database import add_or_update_user, get_all_users
import time
from hash import hash
import uuid

bot = telebot.TeleBot(hash)
channel_username = "@nit_needs"  
JOB_ADMIN_ID = 112911597

# ___________________________________BUTTONS________________________________________________
buttons = [
    "🏷 فروشی", 
    "📎 درخواستی", 
    "🏡 همخونه",
    "📤ارسال جزوه و فایل",
    "🔍 گمشده", 
    "🔎 پیدا شده",
    "💡فرصت شغلی",
    "📩 اطلاعات اساتید", 
    "📈 تبلیغات", 
    "📞 ارتباط با ادمین", 
]

home_button = [
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
admin_messages = {}  # ذخیره message_id هر درخواست برای هر ادمین

# ____________________________________Verfication FUNCTION________________________________________
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

# ____________________________________ADMINS_____________________________________________
admin_roles = {
    112911597: "all", 
    442513360: "all",
    244143516: "all",
    101108999: "all",
    1751472873: "all",  
    1172391323: "all",
    581500840: "all",
    5410322306: "all",  
    101108994: "all",  
    6695777982: "all",     
}

# ____________________________________START & BACK_____________________________________________
@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    username = message.from_user.username
    full_name = message.from_user.first_name + " " + (message.from_user.last_name or "")
    
    add_or_update_user(chat_id, username, full_name)
    
    bot.send_message(chat_id, f"""سلام به ربات نیازمندی‌ها خوش اومدی 🩷
چطوری میتونم بهت کمک کنم؟""", reply_markup=keyboard_markup)

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت")
def back_to_main(message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id] 
        
    if chat_id in timers:
        timers[chat_id].cancel()
        del timers[chat_id]
    
    bot.send_message(chat_id, "به صفحه اصلی بازگشتید.", reply_markup=keyboard_markup)

# ____________________________________REQUEST HANDLER________________________________________
def handle_request(message, hashtag, instruction_text):
    chat_id = message.chat.id
    
    if check_channel_membership(chat_id):
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
        
        timer = Timer(120, timeout_message, [chat_id])    
        timer.start()
        timers[chat_id] = timer

    else:
        send_subscription_prompt(chat_id)

# ____________________________________PROCESS USER REQUEST________________________________________
@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id]["state"] == "waiting_for_message")
def process_user_message(message):
    chat_id = message.chat.id
    user_message = message.text
    hashtag = user_states[chat_id]["hashtag"]
    
    final_message = f"❓{user_message}" if hashtag == "#درخواستی" else f"{hashtag}\n{user_message}"
    request_id = str(uuid.uuid4())

    pending_requests.append({
        "request_id": request_id,  
        "user_id": chat_id,
        "message": final_message,
        "hashtag": hashtag,
        "approved": False
    })

    admin_messages[request_id] = {}

    if hashtag == "#فرصت_شغلی":
        target_admins = [JOB_ADMIN_ID]
    else:
        target_admins = admin_roles.keys()

    for admin_id in target_admins:
        try:
            markup = InlineKeyboardMarkup()
            accept_button = InlineKeyboardButton("✅ تایید", callback_data=f"accept_{request_id}")
            reject_button = InlineKeyboardButton("❌ رد", callback_data=f"reject_{request_id}")
            markup.add(accept_button, reject_button)

            sender_info = f"👤 فرستنده: @{message.from_user.username}" if message.from_user.username else f"👤 فرستنده: {message.from_user.first_name}"

            sent_msg = bot.send_message(
                admin_id,
                f"{sender_info}\n\nدرخواست جدید:\n{final_message}",
                reply_markup=markup
            )

            admin_messages[request_id][admin_id] = sent_msg.message_id

        except Exception as e:
            print(f"خطا در ارسال به ادمین {admin_id}: {e}")

    bot.reply_to(message, "درخواست شما با موفقیت برای بررسی ارسال شد.")
    del user_states[chat_id]

# ____________________________________ADMIN ACTIONS________________________________________
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_admin_action(call):
    action, request_id = call.data.split("_", 1)
    request = next((r for r in pending_requests if r["request_id"] == request_id), None)

    if not request:
        bot.answer_callback_query(call.id, "❗ درخواست پیدا نشد یا قبلاً رسیدگی شده.")
        return

    if request["hashtag"] == "#فرصت_شغلی" and call.from_user.id != JOB_ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ شما مجاز به مدیریت فرصت‌های شغلی نیستید.")
        return

    # حذف پیام از همه ادمین‌ها
    if request_id in admin_messages:
        for admin_id, msg_id in admin_messages[request_id].items():
            try:
                bot.delete_message(admin_id, msg_id)
            except Exception as e:
                print(f"❌ خطا در حذف پیام ادمین {admin_id}: {e}")
        del admin_messages[request_id]

    if action == "accept":
        bot.send_message(channel_username, f"{request['message']}\n")
        safe_send_message(request["user_id"], "✅ درخواستت تایید شد و در کانال منتشر شد.")
        pending_requests.remove(request)

    elif action == "reject":
        bot.answer_callback_query(call.id, "در حال انتظار برای دلیل رد شدن...")
        msg = bot.send_message(call.message.chat.id, "❌ لطفاً دلیل رد شدن این درخواست را وارد کنید:")

        def process_reason(message):
            reason = message.text.strip()
            safe_send_message(request["user_id"], f"❌ درخواستت رد شد.\n📝 دلیل: {reason}")
            pending_requests.remove(request)
            bot.send_message(call.message.chat.id, "✅ درخواست با موفقیت رد شد.", reply_markup=keyboard_markup)

        bot.register_next_step_handler(msg, process_reason)

# ____________________________________UTIL________________________________________
def safe_send_message(chat_id, text, **kwargs):
    try:
        bot.send_message(chat_id, text, **kwargs)
    except telebot.apihelper.ApiTelegramException as e:
        if "Forbidden: bot was blocked by the user" in str(e):
            print(f"❌ کاربر {chat_id} ربات رو بلاک کرده.")
        else:
            print(f"⚠️ خطا در ارسال پیام به {chat_id}: {e}")

# ____________________________________RUN________________________________________
bot.infinity_polling()
