from app.keyboards.inline.base import *
from app.models import Track

pay_track_cb = CallbackData('pay', 'track_id', 'price')
admin_pay_check_cb = CallbackData('paycheck', 'action', 'user_id', 'track_id')


def pay_tracks_kb(tracks: list[Track]):
    inline_keyboard = []
    for track in tracks:
        if track.price != 0:
            inline_keyboard.append([InlineKeyboardButton(
                f'💳 {track.price} грн - {track.title}',
                callback_data=pay_track_cb.new(track_id=track.track_id, price=track.price)
            )])
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)


def admin_pay_check_kb(user_id: int, track_id: int, user_url: str):
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton('Підтвердити ✅',
                                     callback_data=admin_pay_check_cb.new(user_id=user_id, track_id=track_id, action='confirm')),
                InlineKeyboardButton('Скасувати ❌',
                                     callback_data=admin_pay_check_cb.new(user_id=user_id, track_id=track_id, action='abort'))
            ],
            [InlineKeyboardButton('Відкрити чат 📲', url=user_url)]
        ]
    )


def chat_cb(user_url: str):
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton('Відкрити чат 📲', url=user_url)]
        ]
    )
