from aiogram import Dispatcher
from app.handlers.private import (
    pay,
    start,
    post,
    admin,
    sub
)


def setup(dp: Dispatcher):
    sub.setup(dp)
    pay.setup(dp)
    start.setup(dp)
    post.setup(dp)
    admin.setup(dp)


