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
