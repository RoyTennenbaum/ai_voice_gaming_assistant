from unittest.mock import MagicMock, patch
import httpx
import pytest

from ai_voice_gaming_assistant.core import db
from ai_voice_gaming_assistant.data import ingest


def test_fetch_and_store_items_success(initialized_db, sample_items):
    """Test fetching items and inserting them into the database."""
    mock_response = MagicMock()
    mock_response.json.return_value = sample_items
    mock_response.raise_for_status.return_value = None

    with patch("httpx.get", return_value=mock_response) as mock_get:
        ingest.fetch_and_store_items()
        mock_get.assert_called_once_with(ingest.ALL_ITEMS_URL)

    cursor = initialized_db.cursor()
    cursor.execute("SELECT id, name, category, description FROM items")
    db_items = cursor.fetchall()
    assert len(db_items) == len(sample_items)

    # Check that items_fts also has the entries
    cursor.execute("SELECT name, category, description FROM items_fts")
    fts_items = cursor.fetchall()
    assert len(fts_items) == len(sample_items)


def test_store_items_idempotency(initialized_db, sample_items):
    """Test that running store_items multiple times does not create duplicates in items or items_fts."""
    # First population
    ingest.store_items(sample_items)

    # Second population with the exact same data
    ingest.store_items(sample_items)

    cursor = initialized_db.cursor()
    cursor.execute("SELECT count(*) FROM items")
    items_count = cursor.fetchone()[0]
    assert items_count == len(sample_items)

    cursor.execute("SELECT count(*) FROM items_fts")
    fts_count = cursor.fetchone()[0]
    assert fts_count == len(sample_items)


def test_fetch_and_store_items_idempotency(initialized_db, sample_items):
    """Test that calling fetch_and_store_items repeatedly is idempotent."""
    mock_response = MagicMock()
    mock_response.json.return_value = sample_items
    mock_response.raise_for_status.return_value = None

    with patch("httpx.get", return_value=mock_response):
        ingest.fetch_and_store_items()
        ingest.fetch_and_store_items()

    cursor = initialized_db.cursor()
    cursor.execute("SELECT count(*) FROM items")
    assert cursor.fetchone()[0] == len(sample_items)

    cursor.execute("SELECT count(*) FROM items_fts")
    assert cursor.fetchone()[0] == len(sample_items)


def test_fetch_and_store_items_filters_incomplete_data(initialized_db):
    """Test that items with missing name or uniqueName are skipped."""
    raw_data = [
        {"uniqueName": "", "name": "Nameless Item", "category": "Misc", "description": ""},
        {"uniqueName": "/Lotus/Types/NoName", "name": "", "category": "Misc", "description": ""},
        {"uniqueName": "/Lotus/Types/Valid", "name": "Valid Item", "category": "Weapons", "description": "Good"},
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = raw_data
    mock_response.raise_for_status.return_value = None

    with patch("httpx.get", return_value=mock_response):
        ingest.fetch_and_store_items()

    cursor = initialized_db.cursor()
    cursor.execute("SELECT id, name FROM items")
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0] == ("/Lotus/Types/Valid", "Valid Item")


def test_fetch_and_store_items_http_error(initialized_db):
    """Test that an HTTP error raises an exception and doesn't insert data."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=MagicMock(), response=MagicMock(status_code=500)
    )

    with patch("httpx.get", return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            ingest.fetch_and_store_items()


def test_main_runs_init_and_fetch():
    """Test that main() invokes init_db and fetch_and_store_items."""
    with patch("ai_voice_gaming_assistant.data.ingest.init_db") as mock_init, \
         patch("ai_voice_gaming_assistant.data.ingest.fetch_and_store_items") as mock_fetch:
        ingest.main()
        mock_init.assert_called_once()
        mock_fetch.assert_called_once()
