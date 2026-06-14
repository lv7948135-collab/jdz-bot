from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from ai.claude_client import get_analysis
from bot.keyboards.inline import audit_keyboard

router = Router()

MAX_TG_LENGTH = 4096  # лимит Telegram на длину сообщения


async def run_analysis(message: Message, state: FSMContext):
    """
    Финальный шаг: берём все данные из state,
    отправляем в Claude, возвращаем разбор + CTA.
    """
    data = await state.get_data()
    calc_text = data.get("calc_text", "")
    rating    = data.get("rating", "не указан")
    problem   = data.get("problem", "не указана")

    # Показываем "анализирую" пока Claude думает
    thinking = await message.answer(
        "⏳ Анализирую данные...\n\nОбычно занимает 20–30 секунд.",
        reply_markup=ReplyKeyboardRemove()
    )

    result = get_analysis(calc_text, rating, problem)

    # Удаляем сообщение "анализирую"
    try:
        await thinking.delete()
    except Exception:
        pass

    # Отправляем результат (разбиваем если длиннее лимита)
    for chunk in split_text(result, MAX_TG_LENGTH):
        await message.answer(chunk)

    # CTA на платный аудит
    await message.answer(
        "━━━━━━━━━━━━━━━━━━\n"
        "Это бесплатный AI-разбор.\n\n"
        "Полный SKU-аудит включает:\n"
        "• разбор карточки, фото, отзывов\n"
        "• вердикт SCALE / FIX / STOP\n"
        "• план из 2–3 конкретных шагов\n"
        "• срок — до 24 часов\n\n"
        "Стоимость: 14 900 ₽",
        reply_markup=audit_keyboard()
    )

    await state.clear()


def split_text(text: str, max_length: int) -> list[str]:
    """Разбивает длинный текст на части по абзацам."""
    paragraphs = text.split("\n\n")
    chunks, current = [], ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_length:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = para + "\n\n"

    if current:
        chunks.append(current.strip())

    return chunks if chunks else [text[:max_length]]
