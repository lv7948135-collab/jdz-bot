import aiosqlite
import logging
from datetime import datetime

DB_PATH = "jdz.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS consents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                agreed INTEGER DEFAULT 0,
                marketing INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logging.info("✅ База данных инициализирована")

async def save_consent(user_id: int, username: str, full_name: str, agreed: bool, marketing: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO consents (user_id, username, full_name, agreed, marketing, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, int(agreed), int(marketing), datetime.now().isoformat())
        )
        await db.commit()

async def save_message(user_id: int, content: str, role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.now().isoformat())
        )
        await db.commit()

async def delete_user_data(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM consents WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row[0] == 0:
            return False
        await db.execute("DELETE FROM consents WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        await db.commit()
        return True


async def init_metrics_tables() -> None:
    """
    Создаёт таблицы для Metrics Collector (bot_starts, reaction_snapshots).
    Вызывается отдельно от init_db(), чтобы не трогать существующую схему.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_starts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_item_id INTEGER NOT NULL,
                post_code TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, content_item_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reaction_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_item_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                reactions_json TEXT NOT NULL,
                reactions_total INTEGER NOT NULL,
                captured_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logging.info("✅ Таблицы метрик инициализированы (bot_starts, reaction_snapshots)")


async def save_bot_start(user_id: int, content_item_id: int, post_code: str) -> None:
    """Сохранить факт запуска бота по deep-link. INSERT OR IGNORE защищает от повторного учёта."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO bot_starts (user_id, content_item_id, post_code) VALUES (?, ?, ?)",
            (user_id, content_item_id, post_code),
        )
        await db.commit()


async def save_reaction_snapshot(content_item_id: int, chat_id: int, message_id: int, reactions_json: str, reactions_total: int) -> None:
    """Сохранить снимок реакций на сообщение."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reaction_snapshots (content_item_id, chat_id, message_id, reactions_json, reactions_total) VALUES (?, ?, ?, ?, ?)",
            (content_item_id, chat_id, message_id, reactions_json, reactions_total),
        )
        await db.commit()
