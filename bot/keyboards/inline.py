from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)


def start_keyboard() -> InlineKeyboardMarkup:
    """Кнопка запуска анализа на экране /start."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Вставить результат и получить разбор", callback_data="start_analysis")]
    ])


def rating_keyboard() -> ReplyKeyboardMarkup:
    """Быстрый выбор рейтинга карточки."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ ниже 4.0"), KeyboardButton(text="⭐ 4.0 – 4.5")],
            [KeyboardButton(text="⭐ 4.5 – 4.8"), KeyboardButton(text="⭐ выше 4.8")],
            [KeyboardButton(text="Не знаю")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def audit_keyboard() -> InlineKeyboardMarkup:
    """CTA после AI-разбора."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📋 Заказать полный аудит — 14 900 ₽",
            url="https://t.me/Vob75?text=АУДИТ"
        )],
        [InlineKeyboardButton(text="🔄 Разобрать другой товар", callback_data="start_analysis")]
    ])
