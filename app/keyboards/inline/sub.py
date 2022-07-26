from app.keyboards.inline.base import *

stop_sub_cb = CallbackData('stop_sub', 'user_id')
start_sub_cb = CallbackData('start_sub', 'user_id')
admin_sub_check_cb = CallbackData('sub_pay', 'action', 'user_id')


def start_sub_kb(user_id: int):
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton('Оплатити підписку', callback_data=start_sub_cb.new(user_id=user_id))]
        ]
    )


def stop_sub_kb(user_id: int):
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton('Скасувати підписку', callback_data=stop_sub_cb.new(user_id=user_id))]
        ]
    )


def admin_sub_check_kb(user_id: int, user_url: str):
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton('Підтвердити ✅',
                                     callback_data=admin_sub_check_cb.new(user_id=user_id, action='confirm')),
                InlineKeyboardButton('Скасувати ❌',
                                     callback_data=admin_sub_check_cb.new(user_id=user_id, action='abort'))
            ],
            [InlineKeyboardButton('Відкрити чат 📲', url=user_url)]
        ]
    )


__all__ = (
    'stop_sub_kb',
    'start_sub_kb',
    'stop_sub_cb',
    'start_sub_cb',
)
