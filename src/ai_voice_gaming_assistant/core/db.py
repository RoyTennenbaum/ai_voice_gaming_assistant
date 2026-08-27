# Async SQLite connection management and schema setup
import sqlite3
from pathlib import Path

# Save db in the root
DB_PATH = Path("warframe.db")

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT
        )
    """)

    # Full-Text Search for fast, efficient db searches
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
            name,
            category,
            description
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()