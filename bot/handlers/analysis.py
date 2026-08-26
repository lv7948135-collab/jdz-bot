from aiogram import Router
import sys
sys.path.append("/root/djavis-os")
from subscription_service import check_access, record_usage
import asyncio
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from bot.keyboards.inline import contact_keyboard
from ai.claude_client import get_claude_response
from db.database import save_message

_VERDICT_MARKERS = ("🔴 УБЫТОК", "🟡 НУЛЕВАЯ ПРИБЫЛЬ", "🟢 ПРИБЫЛЬ")

router = Router()

@router.message(UserStates.waiting_question)
async def handle_question(message: Message, state: FSMContext):
    decision = await asyncio.to_thread(check_access, message.from_user.id, "alex_ai_analysis")
    if not decision.allowed:
        await message.answer(decision.reason)
        return

    await asyncio.to_thread(record_usage, message.from_user.id, "alex_ai_analysis")
    if not message.text:
        await message.answer("Пожалуйста, отправьте вопрос текстовым сообщением.")
        return

    await save_message(message.from_user.id, message.text, role="user")
    thinking = await message.answer("🔍 Анализирую вашу ситуацию...")

    response = await get_claude_response(message.text)

    await save_message(message.from_user.id, response, role="assistant")
    await thinking.delete()
    markup = contact_keyboard() if any(v in response for v in _VERDICT_MARKERS) else None
    await message.answer(response, parse_mode="HTML", reply_markup=markup)
