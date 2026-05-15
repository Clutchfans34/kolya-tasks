import aiosqlite
import json
from datetime import datetime
from config import DATABASE_PATH

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'todo',
    due_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript(CREATE_TABLES)
        await db.commit()


async def get_tasks(user_id: int, status: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE user_id=? AND status=? ORDER BY due_date ASC, priority DESC, created_at ASC",
                (user_id, status)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE user_id=? ORDER BY due_date ASC, priority DESC, created_at ASC",
                (user_id,)
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def create_task(user_id: int, title: str, description: str = "", priority: str = "medium", due_date: str = None):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (user_id, title, description, priority, status, due_date, created_at, updated_at) VALUES (?, ?, ?, ?, 'todo', ?, ?, ?)",
            (user_id, title, description, priority, due_date, now, now)
        )
        await db.commit()
        return cursor.lastrowid


async def update_task_status(task_id: int, user_id: int, status: str):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE id=? AND user_id=?",
            (status, now, task_id, user_id)
        )
        await db.commit()


async def delete_task(task_id: int, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
        await db.commit()


async def get_stats(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks WHERE user_id=? GROUP BY status",
            (user_id,)
        )
        rows = await cursor.fetchall()
        stats = {"todo": 0, "in_progress": 0, "done": 0}
        for row in rows:
            stats[row[0]] = row[1]
        return stats


async def save_message(user_id: int, role: str, content: str):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, now)
        )
        await db.commit()


async def get_chat_history(user_id: int, limit: int = 20):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return list(reversed([dict(r) for r in rows]))


async def register_contact(user_id: int, name: str):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO contacts (user_id, name, added_at) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET name=?, added_at=?",
            (user_id, name, now, name, now)
        )
        await db.commit()


async def get_contacts():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT user_id, name FROM contacts ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_contact_by_name(name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, name FROM contacts WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{name}%",)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def clear_chat_history(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
        await db.commit()
