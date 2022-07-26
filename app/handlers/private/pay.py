import re

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, CommandStart
from aiogram.types import Message, ChatType, ContentType, CallbackQuery, \
    MediaGroup, InputMediaAudio

from app.config import Config
from app.handlers.private.start import command_start
from app.keyboards.inline.pay import pay_tracks_kb, pay_track_cb, admin_pay_check_kb, admin_pay_check_cb, chat_cb
from app.keyboards.reply.pay import pay_kb
from app.keyboards.reply.post import confirm_kb, cancel_kb, send_kb
from app.services.repos import TrackRepo, PostRepo, Track, SubscriptRepo, UserRepo
from app.states.pay import PaySG

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
            'Оплатіть вартість треку, або виберіть потрібний якщо у вас є "<b>Підписка</b> 💸"',
            reply_markup=pay_tracks_kb(tracks)
        )


async def send_payment(call: CallbackQuery, callback_data: dict, track_db: TrackRepo,
                       state: FSMContext, sub_db: SubscriptRepo, user_db: UserRepo):
    track_id = int(callback_data.get('track_id'))
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

    await call.message.answer('Оберіть тип оплати', reply_markup=pay_kb)
    await state.update_data(track_id=track.track_id)
    await PaySG.Pay.set()


async def card_payment(msg: Message, config: Config, state: FSMContext, track_db: TrackRepo):
    data = await state.get_data()
    track_id = int(data['track_id'])
    track = await track_db.get_tracks_by_track_id(track_id)

    text = (
        f'Наші реквізити за картою\n💳 <code>{config.payment.card}</code>\n\n'
        f'Трек: <b>{track.title}</b>\n'
        f'Сума до оплати: {track.price} грн\n\n'
        f'Проведіть оплату та наділшліть підтверджуюче фото (скріншот)'
    )
    await msg.answer(text=text, reply_markup=cancel_kb)
    await state.update_data(method='банківська карточка')
    await PaySG.Photo.set()


async def paypal_payment(msg: Message, state: FSMContext, config: Config, track_db: TrackRepo):
    data = await state.get_data()
    track_id = int(data['track_id'])
    track = await track_db.get_tracks_by_track_id(track_id)

    text = (
        f'Наші реквізити за PayPal\n💳 <code>💸 {config.payment.paypal}</code>\n'
        f'Трек: <b>{track.title}</b>\n'
        f'Сума до оплати: {track.price} грн\n\n'
        f'Проведіть оплату та наділшліть підтверджуюче фото (скріншот)'
    )
    await msg.answer(text=text, reply_markup=cancel_kb)
    await state.update_data(method='PayPal')
    await PaySG.Photo.set()


async def save_screenshot(msg: Message, state: FSMContext):
    await state.update_data(photo_id=msg.photo[-1].file_id)
    await msg.reply('Фото завантажено')
    await msg.answer('Напишіть своє повне ПІБ (приклад Іван Якович Франко)')
    await PaySG.Name.set()


async def preview_pay_order(msg: Message, state: FSMContext, track_db: TrackRepo):
    data = await state.get_data()
    track_id = int(data['track_id'])
    method = data['method']
    photo_id = data['photo_id']
    track = await track_db.get_tracks_by_track_id(track_id)

    to_admin = (
        f'💵 Платіж від [{msg.from_user.get_mention()}]\n'
        f'ПІБ: <b>{msg.text}</b>\n\n'
        f'Оплата: {method}\n'
        f'Сума до оплати: {track.price} грн\n'
        f'Трек: <b>{track.title}</b>'
    )
    await state.update_data(to_admin=to_admin)
    await msg.bot.send_photo(chat_id=msg.from_user.id, photo=photo_id, caption=to_admin, reply_markup=send_kb)
    await PaySG.Send.set()


async def send_to_admin(msg: Message, state: FSMContext, config: Config):
    data = await state.get_data()
    to_admin = data['to_admin']
    photo_id = data['photo_id']
    track_id = int(data['track_id'])

    reply_markup = admin_pay_check_kb(user_id=msg.from_user.id, track_id=track_id, user_url=msg.from_user.url)
    for admin_id in config.bot.admin_ids:
        await msg.bot.send_photo(chat_id=admin_id, photo=photo_id, caption=to_admin, reply_markup=reply_markup)
    await msg.answer('Дякуємо за покупу! Ваші дані передані адміністрації на перевірку')
    await state.finish()


async def admin_answer(call: CallbackQuery, track_db: TrackRepo, callback_data: dict):
    action = callback_data['action']
    user_id = int(callback_data['user_id'])
    track_id = int(callback_data['track_id'])
    track = await track_db.get_tracks_by_track_id(track_id)
    call.message.from_user.get_mention()

    url = f'tg://user?id={user_id}'

    caption = call.message.caption
    if action == 'confirm':
        media = MediaGroup([InputMediaAudio(track.file_id)])
        await call.bot.send_message(chat_id=user_id, text='\n\nОплата пройшла успішно')
        await call.bot.send_media_group(chat_id=user_id, media=media)
        await call.message.edit_caption(caption=caption + '\n\nОперація: ✅ платіж схвалено', reply_markup=chat_cb(url))
    else:
        await call.message.edit_caption(caption=caption + '\n\nОперація: ❌ платіж скасовано')
        await call.bot.send_message(chat_id=user_id, text='Адміністрація скасувала ваш платіж', reply_markup=chat_cb(url))


def setup(dp: Dispatcher):
    dp.register_message_handler(chose_track, CommandStart(PAY_REGEX), state='*')
    dp.register_callback_query_handler(send_payment, pay_track_cb.filter(), state='*')
    dp.register_message_handler(card_payment, text='💳 Платіж за картою', state=PaySG.Pay)
    dp.register_message_handler(paypal_payment, text='💸 PayPal', state=PaySG.Pay)
    dp.register_message_handler(save_screenshot, content_types=ContentType.PHOTO, state=PaySG.Photo)
    dp.register_message_handler(preview_pay_order, state=PaySG.Name)
    dp.register_message_handler(send_to_admin, state=PaySG.Send)

    dp.register_callback_query_handler(admin_answer, admin_pay_check_cb.filter(), state='*')




