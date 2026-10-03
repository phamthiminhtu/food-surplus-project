import sqlite3
from datetime import datetime

DB_PATH = "donations.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_name TEXT,
            quantity TEXT,
            expiry_date TEXT,
            allergens TEXT,
            storage TEXT,
            confidence TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_donation(data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO donations (food_name, quantity, expiry_date, allergens, storage, confidence, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["food_name"],
        data["quantity"],
        data["expiry_date"],
        ", ".join(data.get("allergens", [])),
        data.get("storage", ""),
        data.get("confidence", ""),
        "pending",
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def get_donations():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM donations ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]
