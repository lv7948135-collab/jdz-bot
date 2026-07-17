"""
bot/handlers/reactions.py

Reaction Handler (шаг 6 плана Дмитрия, Metrics Collector v1.0).

Граница ответственности:
- Слушает апдейты message_reaction_count от Telegram.
- Делает read-only lookup chat_id + message_id -> content_item_id
  напрямую в БД Publication Queue (/root/djavis-os/publication_queue.db).
- Сохраняет снимок реакций через save_reaction_snapshot (db.database бота).
- НЕ импортирует и не вызывает PublicationWorker.
- НЕ пишет и не меняет ничего в Publication Queue — только читает.
"""

import json
import logging

import aiosqlite
from aiogram import Router
from aiogram.types import MessageReactionCountUpdated

from db.database import save_reaction_snapshot

router = Router()

PUBLICATION_QUEUE_DB_PATH = "/root/djavis-os/publication_queue.db"


async def _find_content_item_id(chat_id: int, message_id: int) -> int | None:
    """Read-only поиск content_item_id по chat_id + message_id в Publication Queue."""
    async with aiosqlite.connect(PUBLICATION_QUEUE_DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM publication_queue WHERE telegram_chat_id = ? AND telegram_message_id = ?",
            (str(chat_id), str(message_id)),
        )
        row = await cursor.fetchone()
        return row[0] if row else None


@router.message_reaction_count()
async def handle_reaction_count(event: MessageReactionCountUpdated) -> None:
    chat_id = event.chat.id
    message_id = event.message_id

    content_item_id = await _find_content_item_id(chat_id, message_id)
    if content_item_id is None:
        logging.info(f"Реакция на message_id={message_id} в chat_id={chat_id}: материал не найден в очереди, пропускаем")
        return

    reactions_list = [
        {"type": r.type.emoji if hasattr(r.type, "emoji") else str(r.type), "count": r.total_count}
        for r in event.reactions
    ]
    reactions_total = sum(r.total_count for r in event.reactions)
    reactions_json = json.dumps(reactions_list, ensure_ascii=False)

    await save_reaction_snapshot(
        content_item_id=content_item_id,
        chat_id=chat_id,
        message_id=message_id,
        reactions_json=reactions_json,
        reactions_total=reactions_total,
    )
    logging.info(f"✅ Сохранён снимок реакций для content_item_id={content_item_id}: {reactions_total} реакций")
