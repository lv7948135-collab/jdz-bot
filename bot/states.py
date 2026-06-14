from aiogram.fsm.state import State, StatesGroup


class Survey(StatesGroup):
    waiting_for_calc = State()  # ждём вставку результата калькулятора
    q1_rating = State()         # вопрос 1: рейтинг карточки
    q2_problem = State()        # вопрос 2: главная проблема
