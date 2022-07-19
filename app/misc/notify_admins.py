import logging
from aiogram import Bot


async def on_startup_notify(bot: Bot, admins_ids: tuple[int, ...]):
    for admin in admins_ids:
        try:
            await bot.send_message(admin, "Бот запущений")
        except Exception as err:
            logging.exception(err)
