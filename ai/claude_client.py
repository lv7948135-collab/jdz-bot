import anthropic
from pathlib import Path
from config.settings import ANTHROPIC_API_KEY

# Загружаем system prompt один раз при старте
_prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
SYSTEM_PROMPT = _prompt_path.read_text(encoding="utf-8")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def build_user_message(calc_text: str, rating: str, problem: str) -> str:
    """Собирает итоговый запрос для Claude."""
    return f"""Данные из калькулятора потерь:
{calc_text}

Контекст:
— Рейтинг карточки: {rating}
— Главная проблема: {problem}

Сделай полный JDZ-разбор по структуре."""


def get_analysis(calc_text: str, rating: str, problem: str) -> str:
    """
    Отправляет данные в Claude, возвращает текст анализа.
    При ошибке возвращает понятное сообщение — не падает.
    """
    user_message = build_user_message(calc_text, rating, problem)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    except anthropic.APIConnectionError:
        return "❌ Ошибка соединения с AI. Попробуйте через минуту."
    except anthropic.RateLimitError:
        return "❌ Превышен лимит запросов. Попробуйте через несколько минут."
    except Exception as e:
        return f"❌ Произошла ошибка: {str(e)}"
