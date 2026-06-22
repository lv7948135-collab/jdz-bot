from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.states import Survey
from bot.keyboards.inline import consent_keyboard
from db.database import save_consent, delete_user_data

router = Router()

OWNER_INFO = (
    "Воробьева Любовь Владимировна\n"
    "ИНН: 300700044636\n"
    "Telegram: @Vob75"
)

WELCOME_TEXT = (
    "👋 Привет! Я Алекс — Нейропродавец WB/Ozon.\n\n"
    "Помогаю продавцам Wildberries и Ozon находить скрытые потери прибыли, "
    "ошибки в ценообразовании и риски карточки.\n\n"
    "За 30 секунд покажу, где Ваш товар может терять деньги.\n\n"
    "❌ Потери прибыли\n"
    "❌ Ошибки в расчётах\n"
    "❌ Риски штрафов\n"
    "❌ Слабые места карточки\n\n"
    "📊 Разбор бесплатный.\n\n"
    "———\n\n"
    "📋 Согласие на обработку данных (152-ФЗ)\n\n"
    "Для работы бота я обрабатываю:\n"
    "• Ваш Telegram ID и username\n"
    "• Текст ваших сообщений\n\n"
    f"Оператор данных: {OWNER_INFO}\n\n"
    "Нажимая «Принимаю», вы даёте согласие на обработку персональных данных.\n"
    "Вы можете удалить свои данные командой /delete_me в любое время.\n\n"
    "📄 Документы:\n"
    "• Оферта: https://endearing-starburst-cf8ece.netlify.app/oferta.html\n"
    "• Политика ПДн: https://endearing-starburst-cf8ece.netlify.app/privacy.html\n\n"
    "⚠️ Алекс предоставляет информационно-аналитические рекомендации. "
    "Результаты не являются финансовой или юридической консультацией."
)

def start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принимаю — продолжить", callback_data="consent_accept")],
        [InlineKeyboardButton(text="✅✅ Принимаю + согласен на рассылку", callback_data="consent_accept_promo")],
        [InlineKeyboardButton(text="❌ Отказываюсь", callback_data="consent_decline")],
        [InlineKeyboardButton(text="📄 Оферта", url="https://endearing-starburst-cf8ece.netlify.app/oferta.html")],
        [InlineKeyboardButton(text="🔒 Политика ПДн", url="https://endearing-starburst-cf8ece.netlify.app/privacy.html")]
    ])

def after_consent_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать бесплатный разбор", callback_data="start_analysis")],
        [InlineKeyboardButton(text="🧮 Калькулятор потерь", url="https://endearing-starburst-cf8ece.netlify.app/")],
        [InlineKeyboardButton(text="📩 Связаться с Любовью", url="https://t.me/Vob75")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=start_keyboard())

@router.callback_query(lambda c: c.data in ["consent_accept", "consent_accept_promo"])
async def consent_accepted(callback: CallbackQuery, state: FSMContext):
    promo = callback.data == "consent_accept_promo"
    await save_consent(callback.from_user.id, callback.from_user.username, promo)
    await callback.message.answer(
        "✅ Согласие принято. Спасибо!\n\n"
        "👋 Привет! Я Алекс — Нейропродавец WB/Ozon.\n\n"
        "Большинство продавцов смотрят только на выручку.\n"
        "Я смотрю глубже:\n\n"
        "❌ Потери прибыли\n"
        "❌ Ошибки в расчётах\n"
        "❌ Риски штрафов\n"
        "❌ Слабые места карточки\n"
        "❌ Упущенные точки роста\n\n"
        "📊 Разбор бесплатный. Начнём?",
        reply_markup=after_consent_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "consent_decline")
async def consent_declined(callback: CallbackQuery):
    await callback.message.answer(
        "Вы отказались от обработки данных.\n"
        "Без согласия бот не может работать.\n\n"
        "Если передумаете — напишите /start"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "start_analysis")
async def start_analysis(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Survey.waiting_for_platform)
    await callback.message.answer(
        "Отлично! Начнём диагностику.\n\n"
        "🏪 Шаг 1 из 6: На какой площадке продаёте товар?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🟣 Wildberries", callback_data="platform_wb")],
            [InlineKeyboardButton(text="🔵 Ozon", callback_data="platform_ozon")]
        ])
    )
    await callback.answer()

@router.message(lambda m: m.text == "/delete_me")
async def delete_me(message: Message):
    await delete_user_data(message.from_user.id)
    await message.answer(
        "✅ Ваши данные удалены из системы.\n\n"
        "Если захотите снова воспользоваться ботом — напишите /start"
    )

@router.message(lambda m: m.text == "/privacy")
async def privacy(message: Message):
    await message.answer(
        "📄 Политика обработки персональных данных:\n"
        "https://endearing-starburst-cf8ece.netlify.app/privacy.html\n\n"
        "📋 Публичная оферта:\n"
        "https://endearing-starburst-cf8ece.netlify.app/oferta.html\n\n"
        "✅ Согласие на обработку данных:\n"
        "https://endearing-starburst-cf8ece.netlify.app/consent.html"
    )
