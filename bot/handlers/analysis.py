from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from ai.claude_client import get_claude_response
from db.database import save_message

router = Router()

@router.message(UserStates.waiting_question)
async def handle_question(message: Message, state: FSMContext):
    await save_message(message.from_user.id, message.text, role="user")
    thinking = await message.answer("🔍 Анализирую вашу ситуацию...")

    response = await get_claude_response(message.text)

    await save_message(message.from_user.id, response, role="assistant")
    await thinking.delete()
    await message.answer(response, parse_mode="HTML")
