from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import Message, CallbackQuery

from app.filters.admin import IsAdminFilter
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


async def admin_start(msg: Message):
    await msg.answer('👋 Привіт. Ви є адміністратором. Вам будуть надходити треки для модерації')


async def cancel(call: CallbackQuery, user_db: UserRepo, sub_db: SubscriptRepo):
    await call.message.delete_reply_markup()
    await call.message.answer('Пост скасовано')


def setup(dp: Dispatcher):
    # dp.register_message_handler(admin_start, Command('start'), IsAdminFilter(), state='*')
    dp.callback_query_handler(cancel, text='cancel', state='*')
    dp.register_message_handler(command_start, Command('start'), state='*')
    dp.register_message_handler(cancel_state, text='❌ Відмінити', state='*')
