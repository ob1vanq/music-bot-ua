from app.states.base import *


class PaySG(StatesGroup):
    Pay = State()
    Photo = State()
    Name = State()
    Send = State()


class SubPaySG(StatesGroup):
    Pay = State()
    Photo = State()
    Name = State()
    Send = State()
