import logging
from aiogram import Dispatcher
from app.middlewares.media import MediaMiddleware
from app.middlewares.database import DatabaseMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.environment import EnvironmentMiddleware

from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


def setup(dp: Dispatcher, session_pool: sessionmaker, environments: dict):
    log.info('Handlers are successfully configured')
    dp.setup_middleware(MediaMiddleware())
    dp.setup_middleware(DatabaseMiddleware(session_pool))
    dp.setup_middleware(EnvironmentMiddleware(environments))
    # dp.setup_middleware(ThrottlingMiddleware())


