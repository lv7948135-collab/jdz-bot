from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принимаю — продолжить", callback_data="consent_yes")],
        [InlineKeyboardButton(text="✅✅ Принимаю + согласен на рассылку", callback_data="consent_yes_marketing")],
        [InlineKeyboardButton(text="❌ Отказываюсь", callback_data="consent_no")],
    ])
