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

    # Index to accelerate exact item name lookups and joins (e.g. JOIN drops ON items.name = drops.item).
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)
    """)

    # Full-Text Search for fast, efficient db searches
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
            name,
            category,
            description
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT,
            item TEXT NOT NULL,
            place TEXT NOT NULL,
            rarity TEXT,
            drop_chance REAL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)

    # Index to accelerate searches by item name (e.g. WHERE item = 'Tellurium').
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_drops_item ON drops(item)
    """)

    # Index to accelerate table joins and ID lookups (e.g. JOIN drops ON items.id = drops.item_id).
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_drops_item_id ON drops(item_id)
    """)

    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS drops_fts USING fts5(
            item,
            place,
            rarity,
            drop_chance
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()