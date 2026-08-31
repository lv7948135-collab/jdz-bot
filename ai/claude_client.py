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
import sqlite3
import sys

sys.path.append('/root/djavis-os')

# Фразы, явно означающие "возвратов нет" (пользователь осознанно ввёл 0)
_NO_RETURNS_RE = re.compile(
    r"(?:"
    r"возврат\w*\s+нет"
    r"|нет\s+возврат\w*"
    r"|без\s+возврат\w*"
    r"|возврат\w*\s*:?\s*0\b"
    r"|0\s*%?\s*возврат\w*"
    r")",
    re.IGNORECASE,
)

import ai_engine
import marketplace_service as ms

# ─────────────────────────────────────────────────────────────────────────────
# Детерминированный pre-filter (без LLM/API).
# Обрабатывает только узкие однозначные случаи: приветствия, благодарности,
# запросы о возможностях и статус-запросы.
#
# Безопасность обеспечена двумя условиями одновременно:
# 1. len(user_message) <= _ALEX_MAX_QUICK_LEN — длинные сообщения всегда
#    уходят в existing path (marketplace или LLM).
# 2. ТОЧНОЕ совпадение нормализованной строки с frozenset — НЕ подстрока.
#    Гарантирует: "Привет, почему падает выкуп?" НЕ перехватится.
# ─────────────────────────────────────────────────────────────────────────────

_ALEX_MAX_QUICK_LEN = 60


def _alex_normalize(text: str) -> str:
    """Strip, lowercase, collapse whitespace, remove punctuation."""
    text = text.strip().lower()
    text = re.sub(r"[!?.,:;\"'\-]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


_ALEX_QUICK_RULES: list[tuple[frozenset, str]] = [
    (
        frozenset({
            "привет", "хай", "hello", "hi",
            "привет алекс", "алекс привет",
            "здравствуй", "здравствуйте",
            "доброе утро", "добрый день", "добрый вечер", "доброй ночи",
        }),
        "Привет! Напишите данные вашего товара — цену, себестоимость и комиссию, "
        "и я сразу рассчитаю юнит-экономику.",
    ),
    (
        frozenset({
            "спасибо", "спасибо алекс", "алекс спасибо",
            "спс", "благодарю", "благодарю алекс",
        }),
        "Пожалуйста! Если хотите разобрать экономику — просто напишите данные товара.",
    ),
    (
        frozenset({
            "что ты умеешь", "что умеешь", "что можешь", "чем можешь помочь",
            "помощь", "/help", "как ты помогаешь", "что ты делаешь",
        }),
        (
            "Я — Алекс, консультант по маркетплейсам WB и Ozon.\n\n"
            "Что умею:\n"
            "📊 Рассчитать юнит-экономику (прибыль, маржу, точку безубыточности)\n"
            "🔵 Дать вердикт: прибыльна ли карточка\n"
            "📌 Предложить следующий шаг\n\n"
            "Напишите: цену, себестоимость и комиссию площадки — я сразу посчитаю."
        ),
    ),
    (
        frozenset({
            "ты работаешь", "алекс ты работаешь", "работаешь",
            "ты онлайн", "бот работает", "ты живой", "ты активен",
        }),
        "Да, работаю! Напишите данные вашего товара — рассчитаю юнит-экономику.",
    ),
]


def _alex_quick_reply(user_message: str) -> str | None:
    """Deterministic pre-filter: возвращает ответ или None → existing path."""
    if len(user_message) > _ALEX_MAX_QUICK_LEN:
        return None
    normalized = _alex_normalize(user_message)
    for phrases, reply in _ALEX_QUICK_RULES:
        if normalized in phrases:
            return reply
    return None


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
    "sales_volume": r"(?:объём|план|штук|шт\.?)\D{0,5}(\d+)",
}

REQUIRED_FOR_MARKETPLACE = ("price", "cost_price", "commission_percent")


def _has_explicit_no_returns(text: str) -> bool:
    """True если пользователь явно сообщил, что возвратов нет (0 допустим)."""
    return bool(_NO_RETURNS_RE.search(text))


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


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Hub — trusted deterministic layer (0 LLM).
#
# Inserted AFTER quick/marketplace routes, BEFORE LLM fallback.
# Fail-open: any exception or missing data → None → fall through to call_ai().
# ─────────────────────────────────────────────────────────────────────────────

_KH_DB_PATH = "/root/djavis-os/data/knowledge.db"
_KH_SEARCH_LIMIT = 3


def _kh_extract_field(full_text: str, field: str) -> str:
    """Extract a named field value from concatenated KH chunk text.

    Handles both single-line fields (FIELD: value) and multiline blocks
    (FIELD:\\nvalue...\\n\\nNEXT_FIELD:). Returns '' if the field is absent.
    """
    m = re.search(
        r"^" + re.escape(field) + r":\s*\n?(.*?)(?=\n[A-Z_]{2,}:|\Z)",
        full_text,
        re.MULTILINE | re.DOTALL,
    )
    return m.group(1).strip() if m else ""


def _kh_lookup(user_message: str) -> str | None:
    """Search the DJAVIS Knowledge Hub for a trusted zero-LLM answer.

    Uses knowledge_hub.search() — no raw SQL beyond the document fetch.
    Returns the canonical_answer string, or None to fall through to LLM.

    Time-sensitivity guard (using KH chunk metadata):
      TIME_SENSITIVITY: LOW  → evergreen definition   → safe to return
      TIME_SENSITIVITY: HIGH + CATEGORY: product_offer → owner-confirmed price → safe
      TIME_SENSITIVITY: HIGH + other category          → fall through (conservative)
      TIME_SENSITIVITY: unknown                        → fall through (conservative)

    Fail-open: any exception → None, never raises.
    """
    try:
        from modules import knowledge_hub as kh

        conn = sqlite3.connect(_KH_DB_PATH, timeout=2.0)
        try:
            hits = kh.search(conn, user_message, limit=_KH_SEARCH_LIMIT)
            if not hits:
                return None

            # Find the document that owns the top-ranked chunk.
            top_chunk_id = hits[0]["content_id"]
            doc_row = conn.execute(
                "SELECT document_id FROM knowledge_chunks WHERE id = ?",
                (top_chunk_id,),
            ).fetchone()
            if not doc_row:
                return None

            doc_id = doc_row[0]

            # Concatenate all chunks (ordered) for full field coverage.
            # TIME_SENSITIVITY lives in chunk_index=1; CANONICAL_ANSWER in chunk_index=0.
            chunk_rows = conn.execute(
                "SELECT chunk_text FROM knowledge_chunks "
                "WHERE document_id = ? ORDER BY chunk_index",
                (doc_id,),
            ).fetchall()
            if not chunk_rows:
                return None

            full_text = "\n\n".join(r[0] for r in chunk_rows)

            # Time-sensitivity guard.
            ts = _kh_extract_field(full_text, "TIME_SENSITIVITY")
            cat = _kh_extract_field(full_text, "CATEGORY")
            if ts == "LOW":
                pass  # evergreen definition — safe
            elif ts == "HIGH" and cat == "product_offer":
                pass  # owner-confirmed price — safe
            else:
                return None  # unknown or time-sensitive non-product → LLM

            canonical = _kh_extract_field(full_text, "CANONICAL_ANSWER")
            return canonical if canonical else None

        finally:
            conn.close()

    except Exception:
        return None


async def get_claude_response(user_message: str) -> str:
    """
    Точка входа, которую вызывает bot/handlers/analysis.py.
    Сигнатура не меняется — хендлер бота трогать не нужно.
    """
    quick = _alex_quick_reply(user_message)
    if quick is not None:
        return quick

    metrics = _parse_metrics(user_message)
    has_enough_data = all(f in metrics for f in REQUIRED_FOR_MARKETPLACE)

    if has_enough_data:
        # CR-01: returns_percent обязателен для точного расчёта.
        # Допустимо только если пользователь явно указал число ИЛИ явно сказал "нет возвратов".
        if "returns_percent" not in metrics:
            if _has_explicit_no_returns(user_message):
                metrics["returns_percent"] = 0.0
            else:
                return (
                    "Чтобы рассчитать точную юнит-экономику, мне нужен процент возвратов.\n\n"
                    "Для одежды и обуви на WB это обычно 30–60%.\n"
                    "Если возвратов практически нет — напишите 0.\n\n"
                    "Укажите: какой процент возвратов у вашего товара?"
                )

        marketplace_input = ms.MarketplaceInput(
            platform="wb",
            user_request=user_message,
            metrics=metrics,
        )
        result = await ms.run(marketplace_input)
        return _format_marketplace_result(result)

    # Knowledge Hub: trusted deterministic answer, 0 LLM calls.
    # Falls through transparently on 0 hits, DB unavailable, or any exception.
    kh_answer = _kh_lookup(user_message)
    if kh_answer:
        return kh_answer

    # LLM fallback: KH had no safe answer.
    return await ai_engine.call_ai(SYSTEM_PROMPT, user_message)
