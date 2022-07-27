from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, ChatJoinRequest

from app.keyboards.reply.post import menu_kb
from app.services.repos import UserRepo, SubscriptRepo


async def command_start(msg: Message, user_db: UserRepo, sub_db: SubscriptRepo):
    user = await user_db.get_user(msg.from_user.id)
    if not user:
        await user_db.add(user_id=msg.from_user.id, mention=msg.from_user.get_mention())
        sub = await sub_db.add(user_id=msg.from_user.id)
    text = (
        '👋 Привіт. Через цей бот ви можете додати свій трек до нашої спільноти'
    )
    await msg.answer(text, reply_markup=menu_kb)


async def cancel_state(msg: Message, state: FSMContext, user_db: UserRepo, sub_db: SubscriptRepo):
    await state.finish()
    await msg.answer('Ви відмінили дію')
    await command_start(msg, user_db, sub_db)


async def cancel(call: CallbackQuery):
    await call.message.delete_reply_markup()
    await call.message.answer('Пост скасовано')


def setup(dp: Dispatcher):
    dp.register_message_handler(command_start, CommandStart(), state='*')
    dp.register_callback_query_handler(cancel, text='cancel', state='*')
    dp.register_message_handler(cancel_state, text='❌ Відмінити', state='*')
    dp.register_chat_join_request_handler(process_chat_join_request, state='*')


async def process_chat_join_request(cjr: ChatJoinRequest, sub_db: SubscriptRepo):
    user_id = cjr.from_user.id
    sub = await sub_db.get_sub_by_user_id(user_id=user_id)
    if sub.status:
        await cjr.approve()
        await cjr.bot.send_message(chat_id=user_id, text='Вас додано до чату з платним контентом')
    else:
        await cjr.decline()
        await cjr.bot.send_message(chat_id=user_id, text='Доступ до цього каналу мають тільки користувачи з підпискою')
