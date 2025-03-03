import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

hash ="7926804782:AAEwdUS3bZB0Dvit8Y5NRa8mNaaiCpZQMFM"

bot = telebot.TeleBot(hash)

buttons = ["📎 درخواستی", "🏷 فروشی", "❓پرسش", "🔍 گمشده / پیدا شده", "📚فایل‌های درسی", "📩 اطلاعات اساتید", "📈 تبلیغات", "📞 ارتباط با ادمین"]
keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
keyboard_markup.add(*buttons)

@bot.message_handler(commands=["admin"])
def admin(message):
    if message.from_user.id in [112911597, 101108999]:
        bot.send_message(message.chat.id, "سلام ادمین عزیز! چه کاری داریم؟", reply_markup=keyboard_markup)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, f"سلام به ربات نیازمندی ها خوش اومدی چجوری میتونم بهت کمک کنم؟", reply_markup=keyboard_markup)


bot.infinity_polling()