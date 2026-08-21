import sqlite3
from pathlib import Path
import pytest
from typing import Generator

from ai_voice_gaming_assistant import db


@pytest.fixture
def temp_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture providing a temporary SQLite database path patched into the db module."""
    db_file = tmp_path / "test_warframe.db"
    monkeypatch.setattr(db, "DB_PATH", db_file)
    return db_file


@pytest.fixture
def initialized_db(temp_db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Fixture that initializes the database schema and yields an active connection."""
    db.init_db()
    conn = db.get_connection()
    yield conn
    conn.close()


@pytest.fixture
def sample_items() -> list[dict]:
    """Fixture providing representative Warframe item data for tests."""
    return [
        {
            "uniqueName": "/Lotus/Types/Items/MiscItems/AlloyPlate",
            "name": "Alloy Plate",
            "category": "Resources",
            "description": "Carbon composite plates used for armor reinforcements.",
        },
        {
            "uniqueName": "/Lotus/Types/Items/MiscItems/CipherItem",
            "name": "Razorback Cipher",
            "category": "Gear",
            "description": "Used to hack into the Razorback armada terminal.",
        },
        {
            "uniqueName": "/Lotus/Types/Items/MiscItems/CryptographicAlu",
            "name": "Cryptographic ALU",
            "category": "Resources",
            "description": "Used to build Razorback Ciphers.",
        },
        {
            "uniqueName": "/Lotus/Types/Items/Warframes/Excalibur",
            "name": "Excalibur",
            "category": "Warframes",
            "description": "A perfect balance of mobility and offense.",
        },
    ]
