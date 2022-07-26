import asyncio
import datetime

from aiogram import Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, ContentType
from aiogram.utils.markdown import hide_link

from app.config import Config
from app.filters.admin import IsAdminFilter
from app.handlers.private.start import command_start
from app.keyboards.inline.pay import chat_cb
from app.keyboards.inline.sub import *
from app.keyboards.inline.sub import admin_sub_check_kb, admin_sub_check_cb
from app.keyboards.reply.pay import pay_kb
from app.keyboards.reply.post import cancel_kb, send_kb
from app.models.subscriprion import Subscription
from app.services.repos import SubscriptRepo, UserRepo
from app.states.pay import SubPaySG
from app.states.sub import SubSG

strfrime = '%d.%m.%Y'
thirty = datetime.timedelta(days=30)


async def check_sub(msg: Message, sub_db: SubscriptRepo, config: Config):
    sub = await sub_db.get_sub_by_user_id(msg.from_user.id)
    if sub.status:
        next_pay = sub.last_paid + thirty
        text = (
            'Ви оформили підписку\n\n'
            f'<b>Останній платіж</b>: {sub.last_paid.strftime(strfrime)}\n'
            f'<b>Наступний платіж</b>: {next_pay.strftime(strfrime)}\n'
        )
        await msg.answer(text=text, reply_markup=stop_sub_kb(msg.from_user.id))
    else:
        link = config.misc.telegraph_url
        text = (
            'Ви <b>не оформили</b> підписку\n\n'
            f'🔸 <a href="{link}">Чому підписка це зручно?</a>\n\n'
            'Бажаєте оформити підписку?'
        )
        await msg.answer(text=text, reply_markup=start_sub_kb(msg.from_user.id))


async def send_sub_payment(call: CallbackQuery):
    await call.message.answer('Оберіть тип оплати', reply_markup=pay_kb)
    await SubPaySG.Pay.set()


async def card_sub_payment(msg: Message, config: Config, state: FSMContext):
    data = await state.get_data()

    text = (
        f'Наші реквізити за картою\n💳 <code>{config.payment.card}</code>\n\n'
        f'Сума до оплати: {config.misc.sub_price} грн\n\n'
        f'Проведіть оплату та наділшліть підтверджуюче фото (скріншот)'
    )
    await msg.answer(text=text, reply_markup=cancel_kb)
    await state.update_data(method='банківська карточка')
    await SubPaySG.Photo.set()


async def paypal_sub_payment(msg: Message, state: FSMContext, config: Config):
    text = (
        f'Наші реквізити за PayPal\n💳 <code>💸 {config.payment.paypal}</code>\n'
        f'Сума до оплати: {config.misc.sub_price} грн\n\n'
        f'Проведіть оплату та наділшліть підтверджуюче фото (скріншот)'
    )
    await msg.answer(text=text, reply_markup=cancel_kb)
    await state.update_data(method='PayPal')
    await SubPaySG.Photo.set()


async def preview_sub_pay_order(msg: Message, state: FSMContext, config: Config):
    data = await state.get_data()
    method = data['method']
    photo_id = data['photo_id']

    to_admin = (
        f'💵 Платіж від [{msg.from_user.get_mention()}]\n'
        f'ПІБ: <b>{msg.text}</b>\n\n'
        f'Оплата: {method}\n'
        f'Оплата підписки: {config.misc.sub_price} грн\n'
    )
    await state.update_data(to_admin=to_admin)
    await msg.bot.send_photo(chat_id=msg.from_user.id, photo=photo_id, caption=to_admin, reply_markup=send_kb)
    await SubPaySG.Send.set()


async def save_sub_screenshot(msg: Message, state: FSMContext):
    await state.update_data(photo_id=msg.photo[-1].file_id)
    await msg.reply('Фото завантажено')
    await msg.answer('Напишіть своє повне ПІБ (приклад Іван Якович Франко)')
    await SubPaySG.Name.set()


async def send_sub_to_admin(msg: Message, state: FSMContext, config: Config):
    data = await state.get_data()
    to_admin = data['to_admin']
    photo_id = data['photo_id']

    reply_markup = admin_sub_check_kb(user_url=msg.from_user.url, user_id=msg.from_user.id)
    for admin_id in config.bot.admin_ids:
        await msg.bot.send_photo(chat_id=admin_id, photo=photo_id, caption=to_admin, reply_markup=reply_markup)
    await msg.answer('Дякуємо за покупу! Ваші дані передані адміністрації на перевірку')
    await state.finish()


async def stop_sub(call: CallbackQuery, sub_db: SubscriptRepo, user_db: UserRepo):
    await sub_db.update_subscript(call.from_user.id, status=False)
    await call.message.answer('Підписка скасована')
    await call.message.delete_reply_markup()
    await command_start(call.message, user_db, sub_db)


async def admin_sub_answer(call: CallbackQuery, callback_data: dict, config: Config, sub_db: SubscriptRepo):
    action = callback_data['action']
    user_id = int(callback_data['user_id'])
    call.message.from_user.get_mention()

    url = f'tg://user?id={user_id}'

    caption = call.message.caption
    if action == 'confirm':
        text = (
            'Оплата підписки пройшла успішно!\n'
            'Вам відкрито доступ до каналу з платним контентом\n\n'
            f'{config.misc.sub_channel_url}'
        )
        await sub_db.update_subscript(user_id, status=True)
        await sub_db.update_date_by_user_id(call.from_user.id)
        await call.bot.send_message(chat_id=user_id, text=text)
        await call.message.edit_caption(caption=caption + '\n\nОперація: ✅ платіж схвалено', reply_markup=chat_cb(url))
    else:
        await call.message.edit_caption(caption=caption + '\n\nОперація: ❌ платіж скасовано', reply_markup=chat_cb(url))
        await call.bot.send_message(chat_id=user_id, text='Адміністрація скасувала ваш платіж')


def setup(dp: Dispatcher):
    # dp.register_message_handler(check_subs, Command('start'), IsAdminFilter(), state='*')
    dp.register_message_handler(check_sub, text='Підписка 💸', state='*')
    dp.register_callback_query_handler(send_sub_payment, start_sub_cb.filter(), state='*')
    dp.register_message_handler(card_sub_payment, text='💳 Платіж за картою', state=SubPaySG.Pay)
    dp.register_message_handler(paypal_sub_payment, text='💸 PayPal', state=SubPaySG.Pay)
    dp.register_message_handler(save_sub_screenshot, content_types=ContentType.PHOTO, state=SubPaySG.Photo)
    dp.register_message_handler(preview_sub_pay_order, state=SubPaySG.Name)
    dp.register_message_handler(send_sub_to_admin, state=SubPaySG.Send)

    dp.register_callback_query_handler(stop_sub, stop_sub_cb.filter(), state='*')

    dp.register_callback_query_handler(admin_sub_answer, admin_sub_check_cb.filter(), state='*')


def _payments_param(sub: Subscription, config: Config):
    return dict(
        description='Підписка',
        payload=str(sub.user_id) + str(sub.sub_id),
        provider_token=config.bot.provider_token,
        prices=_return_prices(config.misc.sub_price),
        title='Оплата підписки',
        currency='UAH'
    )


def _return_prices(price: int) -> list[LabeledPrice]:
    return [
        LabeledPrice('Оплата підписки', price * 100)
    ]
