from aiogram import Dispatcher
from app.handlers.private import (
    pay,
    start,
    post,
    admin,
    sub
)


def setup(dp: Dispatcher):
    pay.setup(dp)
    sub.setup(dp)
    start.setup(dp)
    post.setup(dp)
    admin.setup(dp)


