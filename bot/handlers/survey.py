from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.states import Survey
from bot.keyboards.inline import rating_keyboard

router = Router()


@router.message(Survey.waiting_for_calc)
async def receive_calc(message: Message, state: FSMContext):
    """Шаг 1: получаем вставленный результат калькулятора."""
    text = message.text.strip()

    # Проверяем что это похоже на результат калькулятора
    if "₽" not in text or len(text) < 80:
        await message.answer(
            "⚠️ Похоже, это не результат калькулятора.\n\n"
            "Зайди на сайт, посчитай потери и нажми «Скопировать результат». "
            "Затем вставь сюда полный скопированный текст."
        )
        return

    await state.update_data(calc_text=text)
    await state.set_state(Survey.q1_rating)
    await message.answer(
        "✅ Данные получил.\n\n"
        "Два быстрых вопроса — и запускаю разбор.\n\n"
        "1️⃣ Какой рейтинг у карточки, которую анализируем?",
        reply_markup=rating_keyboard()
    )


@router.message(Survey.q1_rating)
async def q1_rating(message: Message, state: FSMContext):
    """Шаг 2: рейтинг карточки."""
    await state.update_data(rating=message.text.strip())
    await state.set_state(Survey.q2_problem)
    await message.answer(
        "2️⃣ Опиши главную проблему своими словами.\n\n"
        "Например: «падает выкуп», «много возвратов», «реклама дорожает», «нет продаж».",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Survey.q2_problem)
async def q2_problem(message: Message, state: FSMContext):
    """Шаг 3: проблема — запускаем анализ."""
    await state.update_data(problem=message.text.strip())
    await state.set_state(None)

    from bot.handlers.analysis import run_analysis
    await run_analysis(message, state)
