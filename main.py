import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from keys import *

hash ="7926804782:AAEwdUS3bZB0Dvit8Y5NRa8mNaaiCpZQMFM"

bot = telebot.TeleBot(hash)

buttons = ["📎 درخواستی", "🏷 فروشی", "❓پرسش", "🔍 گمشده / پیدا شده", "📚فایل‌های درسی", "📩 اطلاعات اساتید", "📈 تبلیغات", "📞 ارتباط با ادمین"]
keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
keyboard_markup.add(*buttons)

faculty = ["علوم پایه", "مکانیک" , "عمران", "شیمی", "صنایع و مواد", "برق و کامپیوتر" ]
faculty_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
faculty_markup.add(*faculty)

professor = []

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
        bot.send_message(message.chat.id, "درخواستی")
    elif message.text == "🏷 فروشی":
        bot.send_message(message.chat.id, "فروشی")
    elif message.text == "❓پرسش":
        bot.send_message(message.chat.id, "پرسش")
    elif message.text == "🔍 گمشده / پیدا شده":
        bot.send_message(message.chat.id, "گمشده / پیدا شده")
    elif message.text == "📚فایل‌های درسی":
        bot.send_message(message.chat.id, "فایل‌های درسی")
    elif message.text == "📩 اطلاعات اساتید":
        bot.send_message(message.chat.id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟",reply_markup=faculty_markup)
    elif message.text == "📈 تبلیغات":
        bot.send_message(message.chat.id, text_tablighat)
    elif message.text == "📞 ارتباط با ادمین":
        bot.send_message(message.chat.id, text_admin)
bot.infinity_polling()