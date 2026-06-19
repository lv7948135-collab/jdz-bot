import anthropic
from config.settings import ANTHROPIC_API_KEY

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — Алекс, AI-консультант по маркетплейсам Wildberries и Ozon.

Твоя задача: анализировать проблемы продавцов с карточками товаров, выявлять причины потерь, 
штрафов, низкой конверсии и давать конкретные рекомендации.

Стиль ответа:
- Коротко и по делу
- Конкретные цифры и действия
- Без воды и общих фраз
- На русском языке

Всегда в конце ответа добавляй блок:
---
💡 Хотите детальный аудит карточки? Напишите @Vob75"""

AI_DISCLAIMER = (
    "\n\n<i>ℹ️ Ответ сформирован с помощью ИИ. Не является финансовой или юридической консультацией.</i>"
)

async def get_claude_response(user_message: str) -> str:
    try:
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        text = message.content[0].text
        return text + AI_DISCLAIMER
    except Exception as e:
        return f"⚠️ Ошибка при обращении к AI: {str(e)}\n\nПопробуйте позже или напишите @Vob75"
