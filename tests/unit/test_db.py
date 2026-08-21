import sqlite3
from pathlib import Path

from ai_voice_gaming_assistant import db


def test_get_connection(temp_db_path: Path):
    """Test that get_connection returns a valid sqlite3 Connection."""
    conn = db.get_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_init_db_creates_tables(temp_db_path: Path):
    """Test that init_db creates both items and items_fts tables."""
    db.init_db()

    conn = db.get_connection()
    cursor = conn.cursor()

    # Query sqlite_master for created tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    assert "items" in tables
    assert "items_fts" in tables

    # Check columns in the items table
    cursor.execute("PRAGMA table_info(items);")
    columns = {row[1] for row in cursor.fetchall()}
    assert columns == {"id", "name", "category", "description"}

    conn.close()


def test_init_db_idempotency(temp_db_path: Path):
    """Test that init_db can be called repeatedly without error."""
    db.init_db()
    db.init_db()  # Should not raise table already exists error

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='items';")
    count = cursor.fetchone()[0]
    assert count == 1
    conn.close()
