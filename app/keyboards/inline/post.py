from aiogram.utils.deep_linking import get_start_link

from app.keyboards.inline.base import *
from app.models import Track

admin_cb = CallbackData('send', 'post_id', sep=':')
price_cb = CallbackData('price', 'post_id', sep=':')
music_cb = CallbackData('listen', 'post_id', sep=':')


def admin_kb(post_id: int, is_free: bool = True):
    if is_free:
        access = 'вимкнені'
    else:
        access = 'увімкнені ✅'

    return InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Розмістити в каналі', callback_data=admin_cb.new(post_id=post_id)),
                InlineKeyboardButton(text='Скасувати', callback_data='cancel')
            ],
            [
                InlineKeyboardButton(text=f'Редагувати треки (Платні: {access})', callback_data=price_cb.new(post_id=post_id))
            ]
        ]
    )


async def music_kb(post_id: int, tracks: list[Track]):
    prices = list(set([track.price for track in tracks]))
    is_free = (0 in prices and len(prices) == 1)
    if is_free:
        return None
    else:
        return InlineKeyboardMarkup(
            row_width=1,
            inline_keyboard=[
                [InlineKeyboardButton(text='Слухати 🎧', url=await get_start_link(f'pay-{post_id}'))]
            ]
        )

exclusive_cb = InlineKeyboardMarkup(
    row_width=1,
    inline_keyboard=[
        [InlineKeyboardButton('Зробити ексклюзивним ⭐️', callback_data='exclusive')]
    ]
)