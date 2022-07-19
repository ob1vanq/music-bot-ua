from app.keyboards.inline.base import *
from app.models import Track

pay_track_cb = CallbackData('pay', 'track_id', 'price')


def pay_tracks_kb(tracks: list[Track]):
    inline_keyboard = []
    for track in tracks:
        if track.price != 0:
            inline_keyboard.append([InlineKeyboardButton(
                f'💳 {track.price} грн - {track.title}',
                callback_data=pay_track_cb.new(track_id=track.track_id, price=track.price)
            )])
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)
