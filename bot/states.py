from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    waiting_consent = State()
    waiting_question = State()
