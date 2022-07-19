import re

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, CommandStart
from aiogram.types import Message, PreCheckoutQuery, ShippingQuery, ChatType, ContentType, CallbackQuery, LabeledPrice, \
    MediaGroup, InputMediaAudio

from app.config import Config
from app.handlers.private.start import command_start
from app.keyboards.inline.pay import pay_tracks_kb, pay_track_cb
from app.services.repos import TrackRepo, PostRepo, Track, SubscriptRepo, UserRepo

PAY_REGEX = re.compile(r'pay-(\d+)')


async def chose_track(msg: Message, deep_link: re.Match,  track_db: TrackRepo, sub_db: SubscriptRepo, state: FSMContext):
    post_id = int(deep_link.groups()[-1])
    tracks = await track_db.get_tracks_by_post_id(post_id)
    sub = await sub_db.get_sub_by_user_id(msg.from_user.id)
    if sub.status:
        await msg.answer('Вартість треку входить в підписку.\nВиберіть порібний аудіозапис 👇',
                         reply_markup=pay_tracks_kb(tracks))
    else:
        await msg.answer(
            'Оплатіть вартість треку, або скористайтеся "<b>Підпискою</b> 💸"',
            reply_markup=pay_tracks_kb(tracks)
        )


async def send_payment(call: CallbackQuery, callback_data: dict, track_db: TrackRepo, config: Config,
                       state: FSMContext, sub_db: SubscriptRepo, user_db: UserRepo):
    track_id = int(callback_data.get('track_id'))
    price = int(callback_data.get('price'))
    track = await track_db.get_tracks_by_track_id(track_id)
    sub = await sub_db.get_sub_by_user_id(call.from_user.id)
    if sub.status:
        media = MediaGroup([InputMediaAudio(track.file_id)])
        await call.bot.send_media_group(
            chat_id=call.from_user.id, media=media
        )
        await state.finish()
        await command_start(call.message, user_db, sub_db)
        return
    await call.bot.send_invoice(chat_id=call.from_user.id, **_payments_param(track, price, config))
    await state.update_data(file_id=track.file_id)


async def shipping_checkout_answer(query: ShippingQuery):
    await query.bot.answer_shipping_query(shipping_query_id=query.id, ok=True)


async def pre_checkout_answer(query: PreCheckoutQuery):
    await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    await query.bot.send_message(chat_id=query.from_user.id, text='Оплата пройшла успішно, чекаю на зарахування коштів')


async def successful_payment(msg: Message, state: FSMContext, sub_db: SubscriptRepo, user_db: UserRepo):
    data = await state.get_data()
    file_id = data['file_id']
    media = MediaGroup([InputMediaAudio(file_id)])
    await msg.answer('Платіж виконано успішно')
    await msg.bot.send_media_group(
        chat_id=msg.from_user.id, media=media
    )
    await command_start(msg, user_db, sub_db)


def setup(dp: Dispatcher):
    dp.register_message_handler(chose_track, CommandStart(PAY_REGEX), state='*')
    dp.register_callback_query_handler(send_payment, pay_track_cb.filter(), state='*')
    dp.register_shipping_query_handler(shipping_checkout_answer, state='*')
    dp.register_pre_checkout_query_handler(pre_checkout_answer, state='*')
    dp.register_message_handler(
        successful_payment, ChatTypeFilter(ChatType.PRIVATE), content_types=ContentType.SUCCESSFUL_PAYMENT, state='*'
    )


def _payments_param(track: Track, price: int, config: Config):
    return dict(
        description=f'Трек: {track.title}',
        payload=track.track_id,
        provider_token=config.bot.provider_token,
        prices=_return_prices(price),
        title=f'{track.title}',
        currency='UAH'
    )


def _return_prices(price: int) -> list[LabeledPrice]:
    return [
        LabeledPrice('Вартість угоди', price * 100)
    ]