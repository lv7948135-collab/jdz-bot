"""
claude_client.py — адаптер Alex-бота к Marketplace Service.

Заменяет прямой вызов CORE (ai_engine.call_ai) на вызов
marketplace_service.run() — как того требовал Дмитрий: Alex
не обращается к CORE напрямую, он клиент Marketplace Service.

Поведение:
1. Пытаемся распознать в тексте пользователя цифры юнит-экономики
   (цена, себестоимость, комиссия и т.д. — как их обычно возвращает
   калькулятор на Netlify после "Скопировать результат").
2. Если распознали достаточно полей — вызываем marketplace_service.run()
   и отдаём диагноз пользователю.
3. Если НЕ распознали (человек просто написал вопрос текстом,
   без цифр) — работаем как раньше, через ai_engine.call_ai()
   с тем же SYSTEM_PROMPT, чтобы ничего не сломать для обычных
   диалогов.
"""

import re
import sys

sys.path.append('/root/djavis-os')

import ai_engine
import marketplace_service as ms

# Старый промпт остаётся здесь для fallback-режима (сценарий 3 выше) —
# он не удалён, просто больше не единственный путь.
SYSTEM_PROMPT = """Ты — Алекс, AI-консультант по маркетплейсам WB и Ozon.

ВАЖНО: Тебе будут переданы уже посчитанные факты (юнит-экономика,
выручка, издержки, вердикт "прибыль"/"убыток") в блоке "ФАКТЫ" —
НЕ пересчитывай их самостоятельно, используй как есть. Твоя задача —
объяснить, что эти цифры значают для продавца, расставить приоритеты
и предложить следующий шаг.

Используй разделы:
🔵 Что стоит контролировать
📌 Следующий шаг
🟢 / 🟡 / 🔴 Вердикт

ЗАПРЕЩЕНО:
- Пересчитывать прибыль самостоятельно
- Писать вводные фразы типа "По введённым данным..."
- Упоминать площадку и её инструменты в блоке "Что хорошо"
- Писать, что реклама "забирает половину наценки" или считать доли
- Писать "развернуться в сторону реальной прибыли"
- Добавлять любые разделы кроме перечисленных выше
- Использовать слова: критически, гарантированно, обязательно, точно
"""

# Ищем пары вида "Цена: 1000" / "цена — 1000" / "price: 1000" и т.п.
_FIELD_PATTERNS = {
    "price": r"(?:цена|price)\D{0,3}([\d\s]+[.,]?\d*)",
    "cost_price": r"(?:себестоимость|cost_?price)\D{0,3}([\d\s]+[.,]?\d*)",
    "commission_percent": r"(?:комисси[яи]|commission)\D{0,3}([\d\s]+[.,]?\d*)",
    "logistics": r"(?:логистик[аи])\D{0,3}([\d\s]+[.,]?\d*)",
    "advertising": r"(?:реклам[аы])\D{0,3}([\d\s]+[.,]?\d*)",
    "returns_percent": r"(?:возврат\w*)\D{0,3}([\d\s]+[.,]?\d*)",
}

REQUIRED_FOR_MARKETPLACE = ("price", "cost_price", "commission_percent")


def _parse_metrics(text: str) -> dict:
    """Пытается вытащить числовые метрики из свободного текста пользователя."""
    metrics = {}
    for field, pattern in _FIELD_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(" ", "").replace(",", ".")
            try:
                metrics[field] = float(raw)
            except ValueError:
                continue
    return metrics


def _format_marketplace_result(result: ms.MarketplaceResult) -> str:
    """Собирает финальный текст ответа пользователю из MarketplaceResult."""
    if result.error:
        return (
            f"⚠️ {result.error}\n\n"
            f"Попробуйте переформулировать данные или напишите @Vob75"
        )

    ue = result.unit_economics
    lines = [
        result.diagnosis.strip(),
        "",
        f"{result.verdict}",
        f"Прибыль на единицу: {ue.get('profit_per_unit')} ₽ "
        f"(маржа {ue.get('profit_margin_percent')}%)",
        f"📌 {result.next_action.get('description', '')}",
    ]
    return "\n".join(l for l in lines if l)


async def get_claude_response(user_message: str) -> str:
    """
    Точка входа, которую вызывает bot/handlers/analysis.py.
    Сигнатура не меняется — хендлер бота трогать не нужно.
    """
    metrics = _parse_metrics(user_message)
    has_enough_data = all(f in metrics for f in REQUIRED_FOR_MARKETPLACE)

    if has_enough_data:
        marketplace_input = ms.MarketplaceInput(
            platform="wb",
            user_request=user_message,
            metrics=metrics,
        )
        result = await ms.run(marketplace_input)
        return _format_marketplace_result(result)

    # Fallback: цифр недостаточно — работаем как раньше, просто отвечаем текстом
    return await ai_engine.call_ai(SYSTEM_PROMPT, user_message)
