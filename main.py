import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from threading import Timer
from keys import *

bot = telebot.TeleBot(hash)
channel_username = "@test_niazmandiha"  

#___________________________________BUTTONS________________________________________________
buttons = ["📎 درخواستی", "🏷 فروشی", "❓پرسش", "🔍 گمشده / پیدا شده", "📚فایل‌های درسی", "📩 اطلاعات اساتید", "📈 تبلیغات", "📞 ارتباط با ادمین"]
keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
keyboard_markup.add(*buttons)

faculty = ["علوم پایه", "مکانیک", "عمران", "شیمی", "صنایع و مواد", "برق و کامپیوتر"]
faculty_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
faculty_markup.add(*faculty)

admins = ["درخواستی ها", "ردشده ها"]
admins_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
admins_markup.add(*admins)

pending_requests = []
user_states = {}

#____________________________________Verfication FUNCTION________________________________________

def check_channel_membership(user_id):
    try:
        status = bot.get_chat_member(channel_username, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False

def send_subscription_prompt(chat_id):
    markup = InlineKeyboardMarkup()
    subscribe_button = InlineKeyboardButton("🔗 عضویت در کانال", url="t.me/test_niazmandiha")
    markup.add(subscribe_button)
    bot.send_message(chat_id, "برای استفاده از ربات ابتدا باید عضو کانال شوید.", reply_markup=markup)

#____________________________________HANDLERS_____________________________________________

admin_roles = {
    112911597: "all", 
    101108999: "درخواستی",  
    102222333: "فروشی",
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
        for idx, request in enumerate(relevant_requests):
            markup = InlineKeyboardMarkup()
            accept_button = InlineKeyboardButton("✅ تایید", callback_data=f"accept_{idx}")
            reject_button = InlineKeyboardButton("❌ رد", callback_data=f"reject_{idx}")
            markup.add(accept_button, reject_button)
            
            bot.send_message(message.chat.id, f"درخواست از کاربر {request['user_id']}:\n{request['message']}", reply_markup=markup)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, f"""سلام به ربات نیازمندی‌ها خوش اومدی 🩷
چطوری میتونم بهت کمک کنم؟""", reply_markup=keyboard_markup)

def handle_request(message, hashtag, instruction_text):
    chat_id = message.chat.id
    if check_channel_membership(chat_id):
        bot.send_message(chat_id, instruction_text)
        user_states[chat_id] = {"state": "waiting_for_message", "hashtag": hashtag}
        timer = Timer(120, timeout_message, [chat_id])
        timer.start()
    else:
        send_subscription_prompt(chat_id)

@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id]["state"] == "waiting_for_message")
def process_user_message(message):
    chat_id = message.chat.id
    user_message = message.text
    hashtag = user_states[chat_id]["hashtag"]
    
    pending_requests.append({
        "user_id": chat_id,
        "message": f"{hashtag}\n{user_message}",
        "hashtag": hashtag,  
        "approved": False
    })
    
    bot.reply_to(message, "درخواست شما با موفقیت برای ادمین ارسال شد. در صورت تایید در کانال منتشر می‌شود.")
    del user_states[chat_id]


@bot.message_handler()
def main(message):
    if message.text == "📎 درخواستی":
        handle_request(message, "#درخواستی", text_darkhasti)
        
    elif message.text == "🏷 فروشی":
        handle_request(message, "#فروشی", text_foroshi)
        
    elif message.text == "❓پرسش":
        handle_request(message, "#پرسش", text_porsesh)
        
    elif message.text == "🔍 گمشده / پیدا شده":
        handle_request(message, "#گمشده_پیدا_شده", text_gomshode)
        
    elif message.text == "📚فایل‌های درسی":
        bot.send_message(message.chat.id, "فایل‌های درسی", reply_markup=faculty_markup)
        
    elif message.text == "📩 اطلاعات اساتید":
        bot.send_message(message.chat.id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟", reply_markup=faculty_markup)

    elif message.text == "📈 تبلیغات":
        bot.send_message(message.chat.id, text_tablighat)

    elif message.text == "📞 ارتباط با ادمین":
        bot.send_message(message.chat.id, text_admin)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_admin_action(call):
    action, idx = call.data.split("_")
    idx = int(idx)
    request = pending_requests[idx]
    
    if action == "accept":
        bot.send_message(channel_id, f"{request['message']}")
        bot.answer_callback_query(call.id, "درخواست تایید شد و به کانال ارسال شد.")
        pending_requests.pop(idx)  
    elif action == "reject":
        bot.send_message(call.message.chat.id, "لطفا دلیل رد شدن را وارد کنید:")
        bot.register_next_step_handler(call.message, lambda msg: process_rejection(msg, idx))

def process_rejection(message, idx):
    reason = message.text
    request = pending_requests[idx]
    user_id = request["user_id"]
    
    bot.send_message(user_id, f"درخواست شما رد شد. دلیل:\n{reason}")
    bot.send_message(message.chat.id, "درخواست با موفقیت رد شد.")
    pending_requests.pop(idx) 

def timeout_message(chat_id):
    if user_states.get(chat_id) == "waiting_for_message":
        bot.send_message(chat_id, """زمان شما برای ارسال پیام تمام شد. لطفاً از قبل پیام خود را آماده کنید و سپس درخواست دهید.
برای شروع مجدد روی /start کلیک کنید.""")
        del user_states[chat_id]

bot.infinity_polling()
