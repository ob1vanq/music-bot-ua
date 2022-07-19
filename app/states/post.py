from app.states.base import *


class PostSG(StatesGroup):
    Audio = State()
    Wrapper = State()
    Year = State()
    Type = State()
    Send = State()
