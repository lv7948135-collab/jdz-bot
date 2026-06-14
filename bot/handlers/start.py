from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import Survey
from bot.keyboards.inline import start_keyboard

router = Router()

WELCOME_TEXT = (
    "👋 Привет! Я JDZ — AI-система для селлеров WB и Ozon.\n\n"
    "Я разбираю экономику карточки и показываю, где товар теряет деньги.\n\n"
    "Как это работает:\n"
    "1️⃣ Зайди на калькулятор → https://endearing-starburst-cf8ece.netlify.app/\n"
    "2️⃣ Введи данные товара и нажми «Посчитать потери»\n"
    "3️⃣ Нажми «Скопировать результат»\n"
    "4️⃣ Вернись сюда и нажми кнопку ниже\n\n"
    "Разбор занимает ~30 секунд. Бесплатно."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=start_keyboard())


@router.callback_query(lambda c: c.data == "start_analysis")
async def start_analysis(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Survey.waiting_for_calc)
    await callback.message.answer(
        "📋 Вставь сюда результат из калькулятора.\n\n"
        "Это текст, который копируется кнопкой «Скопировать результат» на сайте."
    )
    await callback.answer()
