import logging
from aiogram import Dispatcher
from app.handlers import private

log = logging.getLogger(__name__)


def setup(dp: Dispatcher):
    log.info('Handlers are successfully configured')
    private.setup(dp)
