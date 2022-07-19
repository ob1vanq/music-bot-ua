from app.keyboards.inline.base import *
from app.models import Track

track_cb = CallbackData('track', 'track_id')
back_menu_cb = CallbackData('back_to_menu', 'post_id')
back_track_cb = CallbackData('back_to_track', 'post_id')

set_price = CallbackData('set_price', 'track_id')
set_title = CallbackData('set_title', 'track_id')


def tracks_kb(tracks: list[Track], post_id: int):
    inline_keyboard = [
        [
            InlineKeyboardButton(text='🎵 ' + track.title, callback_data=track_cb.new(track_id=str(track.track_id)))
            for track in tracks],
        [InlineKeyboardButton(text='◀️ Назад', callback_data=back_menu_cb.new(post_id=str(post_id)))]
    ]
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)


def edit_track(track: Track):
    return InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f'Встановити ціну: {track.price} грн 💳',
                                     callback_data=set_price.new(track_id=str(track.track_id))),
                InlineKeyboardButton(text='Змінити назву 🖋',
                                     callback_data=set_title.new(track_id=str(track.track_id)))
            ],
            [InlineKeyboardButton(text='◀️ Назад',
                                  callback_data=back_track_cb.new(post_id=str(track.post_id)))]
        ]
    )
