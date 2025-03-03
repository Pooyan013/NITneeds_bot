import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import time
from keys import *

bot = telebot.TeleBot(hash)

#___________________________________BUTTONS________________________________________________
buttons = ["📎 درخواستی", "🏷 فروشی", "❓پرسش", "🔍 گمشده / پیدا شده", "📚فایل‌های درسی", "📩 اطلاعات اساتید", "📈 تبلیغات", "📞 ارتباط با ادمین"]
keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
keyboard_markup.add(*buttons)

faculty = ["علوم پایه", "مکانیک" , "عمران", "شیمی", "صنایع و مواد", "برق و کامپیوتر" ]
faculty_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
faculty_markup.add(*faculty)

professor = []

#____________________________________HANDELERS_____________________________________________

@bot.message_handler(commands=["admin"])
def admin(message):
    if message.from_user.id in [112911597, 101108999]:
        bot.send_message(message.chat.id, "سلام ادمین عزیز! چه کاری داریم؟", reply_markup=keyboard_markup)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, f"""سلام به ربات نیازمندی‌ها خوش اومدی 🩷
چطوری میتونم بهت کمک کنم؟""", reply_markup=keyboard_markup)

@bot.message_handler()
def main(message):
    if message.text == "📎 درخواستی":
        bot.send_message(message.chat.id, text_darkhasti)
        if message.text == "📎 درخواستی":
            time.sleep(120)
            bot.send_message(message.chat.id, """زمان شما برای ارسال پیام تمام شد لطفا از قبل پیام خود را آماده و سپس درخواست دهید
برای شروع مجدد روی /start کلیک کنید""")
        else:
            user_message = message.text  
            modified_message = f"""#درخواستی
            {user_message}"""
            bot.reply_to(message, modified_message)
            bot.send_message(message.chat.id, '''در خواست شما با موفقیت برای ادمین ارسال شد، درصورت تایید درکانال و درغیر این صورت دلیل رد شدن به شما اطلاع داده میشود
                            
درصورت مشاهده هرگونه مشکل ممنون میشم به ایدی @Pooyan013 پیام دهید ''')

    elif message.text == "🏷 فروشی":
        bot.send_message(message.chat.id, text_foroshi)
        time.sleep(120)
        if message.text == "🏷 فروشی":
            bot.send_message(message.chat.id, """زمان شما برای ارسال پیام تمام شد لطفا از قبل پیام خود را آماده و سپس درخواست دهید
برای شروع مجدد روی /start کلیک کنید""")  
        else:
            user_message = message.text  
            modified_message = f"""#فروشی
            {user_message}"""
            bot.reply_to(message, modified_message)
            bot.send_message(message.chat.id, '''در خواست شما با موفقیت برای ادمین ارسال شد، درصورت تایید درکانال و درغیر این صورت دلیل رد شدن به شما اطلاع داده میشود
                         
درصورت مشاهده هرگونه مشکل ممنون میشم به ایدی @Pooyan013 پیام دهید ''')

    elif message.text == "❓پرسش":
        bot.send_message(message.chat.id, text_porsesh)
        time.sleep(120)
        if message.text == "❓پرسش":
            bot.send_message(message.chat.id, """زمان شما برای ارسال پیام تمام شد لطفا از قبل پیام خود را آماده و سپس درخواست دهید
برای شروع مجدد روی /start کلیک کنید""")  
        else:
            user_message = message.text  
            modified_message = f"""#پرسش
            {user_message}"""
            bot.reply_to(message, modified_message)
            bot.send_message(message.chat.id, '''در خواست شما با موفقیت برای ادمین ارسال شد، درصورت تایید درکانال و درغیر این صورت دلیل رد شدن به شما اطلاع داده میشود
                            
    درصورت مشاهده هرگونه مشکل ممنون میشم به ایدی @Pooyan013 پیام دهید ''')
    elif message.text == "🔍 گمشده / پیدا شده":
        bot.send_message(message.chat.id, text_gomshode)
        time.sleep(120)
        if message.text == "🔍 گمشده / پیدا شده":
            bot.send_message(message.chat.id, """زمان شما برای ارسال پیام تمام شد لطفا از قبل پیام خود را آماده و سپس درخواست دهید
برای شروع مجدد روی /start کلیک کنید""")
        else:  
            user_message = message.text  
            modified_message = f"""#درخواستی
            {user_message}"""
            bot.reply_to(message, modified_message)
            bot.send_message(message.chat.id, '''در خواست شما با موفقیت برای ادمین ارسال شد، درصورت تایید درکانال و درغیر این صورت دلیل رد شدن به شما اطلاع داده میشود
                            
    درصورت مشاهده هرگونه مشکل ممنون میشم به ایدی @Pooyan013 پیام دهید ''')

    elif message.text == "📚فایل‌های درسی":
        bot.send_message(message.chat.id, "فایل‌های درسی")

    elif message.text == "📩 اطلاعات اساتید":
        bot.send_message(message.chat.id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟",reply_markup=faculty_markup)

    elif message.text == "📈 تبلیغات":
        bot.send_message(message.chat.id, text_tablighat)

    elif message.text == "📞 ارتباط با ادمین":
        bot.send_message(message.chat.id, text_admin)
bot.infinity_polling()