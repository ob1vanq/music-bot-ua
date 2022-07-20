from app.keyboards.reply.base import *

pay_kb = ReplyKeyboardMarkup(
    row_width=2,
    one_time_keyboard=True,
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('💳 Платіж за картою'),
            KeyboardButton('💸 PayPal')
        ]
    ]
)
