from aiogram import types, Bot
import logging

from aiogram.types import BotCommandScopeChatMember


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        [
            types.BotCommand("start", "[Ре]Старт боту"),
            types.BotCommand('admin', 'Налаштування')
        ]
    )
    logging.info("Установка комманд прошла успішно")


