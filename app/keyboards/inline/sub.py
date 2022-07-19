from app.keyboards.inline.base import *

stop_sub_cb = CallbackData('stop', 'user_id')
start_sub_cb = CallbackData('start', 'user_id')


def start_sub_kb(user_id: int):
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton('Оформити підписку', callback_data=start_sub_cb.new(user_id=user_id))]
        ]
    )


def stop_sub_kb(user_id: int):
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton('Скасувати підписку', callback_data=stop_sub_cb.new(user_id=user_id))]
        ]
    )


__all__ = (
    'stop_sub_kb',
    'start_sub_kb',
    'stop_sub_cb',
    'start_sub_cb',
)
