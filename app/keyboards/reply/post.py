from app.keyboards.reply.base import *

cancel_bt = [KeyboardButton('❌ Відмінити')]

cancel_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=1,
    one_time_keyboard=True,
    keyboard=[cancel_bt]
)

menu_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=2,
    one_time_keyboard=True,
    keyboard=[
        [KeyboardButton('Розмістити трек 🎵')],
        [KeyboardButton('Підписка 💸')]
    ]
)

confirm_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=1,
    one_time_keyboard=True,
    keyboard=[
        [KeyboardButton('✅ Готово')],
        cancel_bt
    ]
)

type_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=2,
    one_time_keyboard=True,
    keyboard=[
        [KeyboardButton('Remix'), KeyboardButton('Official Remix')],
        [KeyboardButton('Original Track'), KeyboardButton('Mashup')],
        [KeyboardButton('Mix'), KeyboardButton('Live Mix')],
        [KeyboardButton('Acapella')]
    ]
)

send_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    row_width=1,
    keyboard=[
        [KeyboardButton('Відправити ⤴️')],
        cancel_bt
    ]
)

