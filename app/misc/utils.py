
import datetime

from aiogram import Bot

from app.config import Config
from app.keyboards.inline.sub import start_sub_kb
from app.services.repos import SubscriptRepo


async def check_subs(bot: Bot, sub_db: SubscriptRepo, config: Config):
    thirty = datetime.timedelta(days=30)
    subscriptions = await sub_db.get_active_users()
    for sub in subscriptions:
        if sub.status:
            pay_data = (sub.last_paid + thirty)
            now = datetime.datetime.now()
            if now >= pay_data:
                try:
                    await bot.ban_chat_member(chat_id=config.misc.sub_channel_chat_id, user_id=sub.user_id)
                except:
                    pass
                await bot.send_message(
                    chat_id=sub.user_id, text='Прийшов час платити підписку', reply_markup=start_sub_kb(sub.user_id)
                )




