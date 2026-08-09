import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "finassist_memory.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            language_preference TEXT,
            schemes_checked TEXT,
            financial_goal TEXT,
            last_interaction TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_user(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)

    return None


def save_user(
    user_id: str,
    name: str,
    language_preference: str = "",
    schemes_checked: str = "",
    financial_goal: str = ""
):
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        INSERT INTO users (
            user_id,
            name,
            language_preference,
            schemes_checked,
            financial_goal,
            last_interaction
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            schemes_checked = excluded.schemes_checked,
            financial_goal = excluded.financial_goal,
            last_interaction = excluded.last_interaction
    """, (
        user_id,
        name,
        language_preference,
        schemes_checked,
        financial_goal,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
