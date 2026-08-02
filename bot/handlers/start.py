from bot.bot_instance import bot
from bot.keyboards import main_menu
from bot.services.users import add_or_update_user


@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    username = message.from_user.username
    full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}"

    add_or_update_user(chat_id, username, full_name)

    bot.send_message(
        chat_id,
        "سلام به ربات نیازمندی‌ها خوش اومدی 🩷\nچطوری میتونم بهت کمک کنم؟",
        reply_markup=main_menu,
    )
