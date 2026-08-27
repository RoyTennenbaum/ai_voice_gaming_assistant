from unittest.mock import MagicMock, patch

from ai_voice_gaming_assistant.core import db
from ai_voice_gaming_assistant.data import ingest


def test_full_ingest_and_search_flow(temp_db_path, sample_items):
    """Test the complete workflow: init_db -> fetch_and_store_items -> search."""
    mock_response = MagicMock()
    mock_response.json.return_value = sample_items
    mock_response.raise_for_status.return_value = None

    # Initialize database
    db.init_db()

    # Ingest data (with mocked HTTP response)
    with patch("httpx.get", return_value=mock_response):
        ingest.fetch_and_store_items()

    # Connect and perform FTS search
    conn = db.get_connection()
    cursor = conn.cursor()

    # Search for 'armor' which is in Alloy Plate's description
    cursor.execute("SELECT name, category FROM items_fts WHERE items_fts MATCH ?", ("armor",))
    results = cursor.fetchall()

    assert len(results) == 1
    assert results[0] == ("Alloy Plate", "Resources")

    # Verify primary items table integrity
    cursor.execute("SELECT name, category FROM items WHERE id = ?", (sample_items[0]["uniqueName"],))
    item = cursor.fetchone()
    assert item == ("Alloy Plate", "Resources")

    conn.close()
