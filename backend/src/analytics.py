import sqlite3
import os
from datetime import datetime

# Always use the database in the backend folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "call_analytics.db")


def init_db():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            ended_at TEXT NOT NULL,
            outcome TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def record_call(outcome):
    conn = sqlite3.connect(DB_NAME)

    now = datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO calls (started_at, ended_at, outcome)
        VALUES (?, ?, ?)
        """,
        (now, now, outcome)
    )

    conn.commit()
    conn.close()


def get_call_stats():
    conn = sqlite3.connect(DB_NAME)

    total = conn.execute(
        "SELECT COUNT(*) FROM calls"
    ).fetchone()[0]

    successful = conn.execute(
        "SELECT COUNT(*) FROM calls WHERE outcome = 'successful'"
    ).fetchone()[0]

    failed = conn.execute(
        "SELECT COUNT(*) FROM calls WHERE outcome = 'failed'"
    ).fetchone()[0]

    conn.close()

    return {
        "total": total,
        "successful": successful,
        "failed": failed
    }
