from app.states.base import *


class AdminSG(StatesGroup):
    Track = State()
    Edit = State()
    Title = State()
    Price = State()

    Settings = State()