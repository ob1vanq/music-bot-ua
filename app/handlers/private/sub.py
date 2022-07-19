import asyncio
import datetime

from aiogram import Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, ContentType, ShippingQuery, PreCheckoutQuery

from app.config import Config
from app.filters.admin import IsAdminFilter
from app.handlers.private.start import command_start
from app.keyboards.inline.sub import *
from app.models.subscriprion import Subscription
from app.services.repos import SubscriptRepo, UserRepo
from app.states.sub import SubSG

strfrime = '%d.%m.%Y'
thirty = datetime.timedelta(days=30)


async def check_sub(msg: Message, sub_db: SubscriptRepo):
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
        text = (
            'Ви не оформили підписку\n'
            '<i>*інформація чому її треба придбати*</i>\n\n'
            'Бажаєте оформити підписку?'
        )
        await msg.answer(text=text, reply_markup=start_sub_kb(msg.from_user.id))


async def start_sub(call: CallbackQuery, sub_db: SubscriptRepo, config: Config):
    sub = await sub_db.get_sub_by_user_id(call.from_user.id)
    await call.message.answer(
        'Будь ласка оплатіть підписку'
    )
    await call.bot.send_invoice(chat_id=call.from_user.id, **_payments_param(sub, config))
    await SubSG.Pay.set()


async def shipping_checkout_answer(query: ShippingQuery):
    await query.bot.answer_shipping_query(shipping_query_id=query.id, ok=True)


async def pre_checkout_answer(query: PreCheckoutQuery):
    await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    await query.bot.send_message(chat_id=query.from_user.id, text='Оплата пройшла успішно, чекаю на зарахування коштів')


async def successful_payment_sub(msg: Message, sub_db: SubscriptRepo, user_db: UserRepo, state: FSMContext):
    await sub_db.update_date_by_user_id(msg.from_user.id)
    await sub_db.update_subscript(msg.from_user.id, status=True)
    await msg.answer('Вітаю, підписка оплачена')
    await state.finish()
    # await msg.delete_reply_markup()
    await command_start(msg, user_db, sub_db)


async def stop_sub(call: CallbackQuery, sub_db: SubscriptRepo, user_db: UserRepo):
    await sub_db.update_subscript(call.from_user.id, status=False)
    await call.message.answer('Підписка скасована')
    await call.message.delete_reply_markup()
    await command_start(call.message, user_db, sub_db)


def setup(dp: Dispatcher):
    dp.register_message_handler(check_sub, text='Підписка 💸', state='*')

    dp.register_callback_query_handler(start_sub, start_sub_cb.filter(), state='*')
    dp.register_callback_query_handler(stop_sub, stop_sub_cb.filter(), state='*')

    dp.register_shipping_query_handler(shipping_checkout_answer, state=SubSG.Pay)
    dp.register_pre_checkout_query_handler(pre_checkout_answer, state=SubSG.Pay)
    dp.register_message_handler(
        successful_payment_sub, content_types=ContentType.SUCCESSFUL_PAYMENT, state=SubSG.Pay
    )
    dp.register_message_handler(check_subs, Command('start_sub'), IsAdminFilter(), state='*')


async def check_subs(msg: Message, sub_db: SubscriptRepo, config: Config):
    bot = msg.bot
    while True:
        subscriptions = await sub_db.get_active_users()
        for sub in subscriptions:
            if sub.status:
                pay_data = (sub.last_paid + thirty)
                now = datetime.datetime.now()
                if now >= pay_data:
                    await bot.send_message(
                        chat_id=sub.user_id, text='Прийшов час платити підписку'
                    )
                    await bot.send_invoice(chat_id=sub.user_id, **_payments_param(sub, config))
                    await SubSG.Pay.set()
        await asyncio.sleep(86000)


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
