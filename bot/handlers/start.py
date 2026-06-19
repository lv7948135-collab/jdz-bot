from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from bot.keyboards.inline import consent_keyboard
from db.database import save_consent, delete_user_data

router = Router()

OWNER_INFO = (
    "Воробьева Любовь Владимировна\n"
    "ИНН: 300700044636\n"
    "Telegram: @Vob75"
)

CONSENT_TEXT = (
    "👋 Привет! Я Алекс — AI-консультант по маркетплейсам WB и Ozon.\n\n"
    "⚠️ <b>Важно:</b> Алекс предоставляет информационно-аналитические рекомендации "
    "по карточкам товаров. Полученные результаты не являются финансовой, юридической "
    "или инвестиционной консультацией. Окончательные решения вы принимаете самостоятельно.\n\n"
    "📋 <b>Согласие на обработку данных (152-ФЗ)</b>\n\n"
    "Для работы бота я обрабатываю:\n"
    "• Ваш Telegram ID и username\n"
    "• Текст ваших сообщений\n\n"
    f"Оператор данных: {OWNER_INFO}\n\n"
    "Нажимая «Принимаю», вы даёте согласие на обработку персональных данных.\n"
    "Вы можете удалить свои данные командой /delete_me в любое время."
)

PRIVACY_TEXT = (
    "🔒 <b>Политика конфиденциальности</b>\n\n"
    f"Оператор: {OWNER_INFO}\n\n"
    "<b>Какие данные собираются:</b>\n"
    "• Telegram ID и username\n"
    "• Тексты сообщений для анализа\n"
    "• Факт и дата согласия\n\n"
    "<b>Цель обработки:</b> предоставление консультаций по маркетплейсам.\n\n"
    "<b>Хранение:</b> данные хранятся на защищённом сервере.\n\n"
    "<b>Ваши права:</b>\n"
    "• Удалить все данные: /delete_me\n"
    "• Запросить копию данных: напишите @Vob75\n\n"
    "⚠️ Ответы бота не являются финансовой, юридической или инвестиционной консультацией. "
    "Окончательные решения вы принимаете самостоятельно.\n\n"
    "Основание: Федеральный закон №152-ФЗ «О персональных данных»."
)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_consent)
    await message.answer(CONSENT_TEXT, reply_markup=consent_keyboard(), parse_mode="HTML")

@router.message(Command("privacy"))
async def cmd_privacy(message: Message):
    await message.answer(PRIVACY_TEXT, parse_mode="HTML")

@router.message(Command("delete_me"))
async def cmd_delete_me(message: Message, state: FSMContext):
    deleted = await delete_user_data(message.from_user.id)
    await state.clear()
    if deleted:
        await message.answer(
            "✅ Все ваши данные удалены из системы.\n\n"
            "Если захотите снова воспользоваться ботом — нажмите /start."
        )
    else:
        await message.answer("ℹ️ Данных не найдено. Возможно, вы ещё не давали согласие.")

@router.callback_query(F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery, state: FSMContext):
    await save_consent(callback.from_user.id, callback.from_user.username,
                       callback.from_user.full_name, agreed=True, marketing=False)
    await state.set_state(UserStates.waiting_question)
    await callback.message.edit_text(
        "✅ Спасибо! Согласие принято.\n\n"
        "Опишите вашу проблему с карточкой на WB или Ozon — я проанализирую и дам рекомендации.\n\n"
        "<i>Вы можете написать: потери, низкая конверсия, штрафы, проблемы с выкупом или возвратами.</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "consent_yes_marketing")
async def consent_yes_marketing(callback: CallbackQuery, state: FSMContext):
    await save_consent(callback.from_user.id, callback.from_user.username,
                       callback.from_user.full_name, agreed=True, marketing=True)
    await state.set_state(UserStates.waiting_question)
    await callback.message.edit_text(
        "✅ Спасибо! Согласие принято (включая рассылку).\n\n"
        "Опишите вашу проблему с карточкой на WB или Ozon — я проанализирую и дам рекомендации.\n\n"
        "<i>Вы можете написать: потери, низкая конверсия, штрафы, проблемы с выкупом или возвратами.</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "consent_no")
async def consent_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Вы отказались от обработки данных.\n\n"
        "Без согласия бот не может работать.\n"
        "Если передумаете — нажмите /start."
    )
    await callback.answer()
