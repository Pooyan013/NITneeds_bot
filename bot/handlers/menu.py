from bot.bot_instance import bot
try:
    from bot.content import faculty_contacts
except ImportError:
    from bot.content import faculty_contacts_public as faculty_contacts

from bot.content import texts
from bot.handlers.requests import handle_request
from bot.handlers.subscription import is_channel_member, send_subscription_prompt
from bot.keyboards import back_menu, faculty_menu, home_menu, main_menu
from bot.state import timers, user_states

_MEMBERSHIP_GATED_TEXTS = {
    "📤ارسال جزوه و فایل": lambda chat_id: bot.send_message(chat_id, texts.text_send, reply_markup=back_menu),
    "📩 اطلاعات اساتید": lambda chat_id: bot.send_message(
        chat_id, "در مورد استاد کدوم دانشکده میخوای اطلاعات بدم؟", reply_markup=faculty_menu
    ),
    "📈 تبلیغات": lambda chat_id: bot.send_message(chat_id, texts.text_tablighat),
    "📞 ارتباط با ادمین": lambda chat_id: bot.send_message(chat_id, texts.text_admin),
}

_FACULTY_TEXTS = {
    "برق و کامپیوتر": faculty_contacts.bargh_facility,
    "علوم پایه": faculty_contacts.paye_facility,
    "معارف": faculty_contacts.maaref_facility,
}


@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت")
def back_to_main(message):
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

    timer = timers.pop(chat_id, None)
    if timer:
        timer.cancel()

    bot.send_message(chat_id, "به صفحه اصلی بازگشتید.", reply_markup=main_menu)


@bot.message_handler()
def route_text(message):
    chat_id = message.chat.id
    text = message.text

    if text in _MEMBERSHIP_GATED_TEXTS:
        if not is_channel_member(chat_id):
            send_subscription_prompt(chat_id)
            return
        _MEMBERSHIP_GATED_TEXTS[text](chat_id)
        return

    if text == "❓ درخواستی":
        handle_request(message, "#درخواستی", texts.text_darkhasti)
    elif text == "🏷 فروشی":
        handle_request(message, "#فروشی", texts.text_foroshi)
    elif text == "🏡 همخونه":
        bot.send_message(chat_id, "لطفاً انتخاب کنید:", reply_markup=home_menu)
    elif text == "👧همخونه دختر":
        handle_request(message, "#همخونه_دختر", "لطفاً متن درخواست همخونه دختر خود را وارد کنید:")
    elif text == "👦همخونه پسر":
        handle_request(message, "#همخونه_پسر", "لطفاً متن درخواست همخونه پسر خود را وارد کنید:")
    elif text == "🔍 گمشده":
        handle_request(message, "#گمشده", texts.text_gomshode)
    elif text == "🔎 پیدا شده":
        handle_request(message, "#پیدا_شده", texts.text_peyda_shode)
    elif text == "💡فرصت شغلی":
        handle_request(message, "#فرصت_شغلی", texts.text_job)
    elif text in _FACULTY_TEXTS:
        bot.send_message(chat_id, _FACULTY_TEXTS[text])
