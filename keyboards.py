# -*- coding: utf-8 -*-
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


button_hi = KeyboardButton('Начать работу')

button_get = KeyboardButton('Раскрытие номера')
button_bl = KeyboardButton('Добавление номера в BL')
button_remove_member = KeyboardButton('Выкидывание из очереди добавочного')
button4 = KeyboardButton('Кто пропустил')
button_record = KeyboardButton('Выгрузить звуковой файл по звонку')

back_button = KeyboardButton('Вернуться ко всем командам')
hour_ban_button = KeyboardButton('Забанить на час')
button_yes = KeyboardButton('Да')
button_no = KeyboardButton('Нет')
button_for_ok = KeyboardButton('Для ОК')
button_ok_statistic = KeyboardButton('Статистика по анкетам')
button_ok_canseled = KeyboardButton('Кто завершил')


inline_button1 = InlineKeyboardButton('Забанить на час', callback_data='hour')

greet_kb_hi = ReplyKeyboardMarkup(resize_keyboard=True).add(button_hi)
greet_kb_main = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True
                                    ).add(button_get, button_bl).add(button_remove_member).add(button_record).add(button_for_ok)
greet_kb_back = ReplyKeyboardMarkup(resize_keyboard=True).add(back_button)
greet_kb_bl = ReplyKeyboardMarkup(resize_keyboard=True).add(hour_ban_button).add(back_button)
greet_yes_no = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no).add(back_button)
greet_ok = ReplyKeyboardMarkup(resize_keyboard=True).add(button_ok_statistic, button_ok_canseled).add(back_button)

inline_kb1 = InlineKeyboardMarkup().add(inline_button1)


def construct_inline_buttons(dicts: dict):
    inline_button = InlineKeyboardMarkup()
    for i in dicts:
        inline_button = inline_button.add(InlineKeyboardButton(f"{dicts[i]['calldate']} на {dicts[i]['userinterface']}",
                                                               callback_data=f"{dicts[i]['uniqueid']}"))
    return inline_button


def construct_inline_buttons_cancel():
    buttons = {'Входящий': 'cancel_in', 'Исходящий': 'cancel_out'}
    inline_button = InlineKeyboardMarkup()
    for i in buttons:
        inline_button = inline_button.add(InlineKeyboardButton(f"{i}",
                                                               callback_data=f"{buttons[i]}"))
    return inline_button
# markup01 = KeyboardButton('Раскрытие номера')
# markup02 = KeyboardButton('Добавление номера в BL')
# markup03 = KeyboardButton('Выкидывание из очереди добавочного')
# markup04 = KeyboardButton('Кто пропустил')
# markup05 = KeyboardButton('Выгрузить звуковой файл по звонку')
