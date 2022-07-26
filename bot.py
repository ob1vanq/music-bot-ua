import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import AllowedUpdates, ParseMode

from app import filters, handlers, middlewares
from app.config import Config
from app.misc.set_bot_commands import set_default_commands
from app.misc.notify_admins import on_startup_notify
from app.misc.utils import check_subs
from app.services import create_db_engine_and_session_pool
from app.services.repos import SubscriptRepo

log = logging.getLogger(__name__)


async def main():
    config = Config.from_env()
    log_level = config.misc.log_level
    logging.basicConfig(
        level=config.misc.log_level,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    log.info('Starting bot...')

    loop = asyncio.get_event_loop()
    storage = RedisStorage2(host=config.redis.host, port=config.redis.port, loop=loop)
    bot = Bot(config.bot.token, parse_mode=ParseMode.HTML, loop=loop)
    dp = Dispatcher(bot, storage=MemoryStorage(), loop=loop)
    db_engine, sqlalchemy_session_pool = await create_db_engine_and_session_pool(config.db.sqlalchemy_url, log_level)

    allowed_updates: list[str] = AllowedUpdates.MESSAGE + AllowedUpdates.CALLBACK_QUERY + \
                                 AllowedUpdates.MY_CHAT_MEMBER +AllowedUpdates.EDITED_MESSAGE + \
                                 AllowedUpdates.CHAT_JOIN_REQUEST

    environments = dict(config=config)

    middlewares.setup(dp, sqlalchemy_session_pool, environments)
    filters.setup(dp)
    handlers.setup(dp)

    await set_default_commands(bot)
    await on_startup_notify(bot, config.bot.admin_ids)

    scheduler = AsyncIOScheduler()
    kwargs = dict(bot=bot, sub_db=SubscriptRepo(sqlalchemy_session_pool), config=config)
    scheduler.add_job(func=check_subs, trigger='interval', seconds=86000, kwargs=kwargs)
    scheduler.start()

    try:
        await dp.skip_updates()
        await dp.start_polling(allowed_updates=allowed_updates, reset_webhook=True)
    finally:
        await storage.close()
        await storage.wait_closed()
        await (await bot.get_session()).close()
        await db_engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.warning('Bot stopped!')
