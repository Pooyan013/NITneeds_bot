import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import time
from threading import Timer
from keys import *

bot = telebot.TeleBot(hash)

#___________________________________BUTTONS________________________________________________
buttons = ["📎 درخواستی", "🏷 فروشی", "❓پرسش", "🔍 گمشده / پیدا شده", "📚فایل‌های درسی", "📩 اطلاعات اساتید", "📈 تبلیغات", "📞 ارتباط با ادمین"]
keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
keyboard_markup.add(*buttons)

faculty = ["علوم پایه", "مکانیک", "عمران", "شیمی", "صنایع و مواد", "برق و کامپیوتر"]
faculty_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
faculty_markup.add(*faculty)

professor = []

user_states = {}

def timeout_message(chat_id):
    if user_states.get(chat_id) == "waiting_for_message":
        bot.send_message(chat_id, """زمان شما برای ارسال پیام تمام شد. لطفاً از قبل پیام خود را آماده کنید و سپس درخواست دهید.
برای شروع مجدد روی /start کلیک کنید.""")
        del user_states[chat_id] 

#____________________________________HANDLERS_____________________________________________

@bot.message_handler(commands=["admin"])
def admin(message):
    if message.from_user.id in [112911597, 101108999]:
        bot.send_message(message.chat.id, "سلام ادمین عزیز! چه کاری داریم؟", reply_markup=keyboard_markup)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, f"""سلام به ربات نیازمندی‌ها خوش اومدی 🩷
چطوری میتونم بهت کمک کنم؟""", reply_markup=keyboard_markup)

def handle_request(message, hashtag, instruction_text):
    chat_id = message.chat.id
    bot.send_message(chat_id, instruction_text)
    user_states[chat_id] = {"state": "waiting_for_message", "hashtag": hashtag}
    timer = Timer(120, timeout_message, [chat_id])
    timer.start()

@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id]["state"] == "waiting_for_message")
def process_user_message(message):
    chat_id = message.chat.id
    user_message = message.text
    
    hashtag = user_states[chat_id]["hashtag"]
    
    modified_message = f"""{hashtag}\n{user_message}"""
    
    bot.reply_to(message, modified_message)
    
    bot.send_message(chat_id, '''درخواست شما با موفقیت برای ادمین ارسال شد. در صورت تایید در کانال منتشر می‌شود.
در صورت عدم تایید، دلیل رد شدن به شما اطلاع داده خواهد شد.
                         
در صورت مشاهده هرگونه مشکل، لطفاً به آیدی @Pooyan013 پیام دهید.''')
    
    if chat_id in user_states:
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
        bot.send_message(message.chat.id, "فایل‌های درسی")
        
    elif message.text == "📩 اطلاعات اساتید":
        bot.send_message(message.chat.id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟", reply_markup=faculty_markup)

    elif message.text == "📈 تبلیغات":
        bot.send_message(message.chat.id, text_tablighat)

    elif message.text == "📞 ارتباط با ادمین":
        bot.send_message(message.chat.id, text_admin)


bot.infinity_polling()
