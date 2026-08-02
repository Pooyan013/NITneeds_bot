from telebot.types import ReplyKeyboardMarkup

from bot.content.texts import (
    ADMIN_BUTTONS,
    BACK_BUTTON,
    FACULTY_BUTTONS,
    HOME_BUTTONS,
    MAIN_MENU_BUTTONS,
)

main_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_menu.add(*MAIN_MENU_BUTTONS)

home_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
home_menu.add(*HOME_BUTTONS)

faculty_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
faculty_menu.add(*FACULTY_BUTTONS)

admin_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
admin_menu.add(*ADMIN_BUTTONS)

back_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
back_menu.add(BACK_BUTTON)
