from unittest.mock import patch

from ai_voice_gaming_assistant.data import ingest


def test_store_items_inserts_correctly(initialized_db, sample_items):
    """Test that store_items populates both items and items_fts tables."""
    ingest.store_items(sample_items)

    cursor = initialized_db.cursor()

    cursor.execute("SELECT id, name, category, description FROM items")
    db_items = cursor.fetchall()
    assert len(db_items) == len(sample_items)

    cursor.execute("SELECT name, category, description FROM items_fts")
    fts_items = cursor.fetchall()
    assert len(fts_items) == len(sample_items)


def test_store_items_idempotency(initialized_db, sample_items):
    """Test that running store_items multiple times does not create duplicates in items or items_fts."""
    ingest.store_items(sample_items)
    ingest.store_items(sample_items)

    cursor = initialized_db.cursor()
    cursor.execute("SELECT count(*) FROM items")
    assert cursor.fetchone()[0] == len(sample_items)

    cursor.execute("SELECT count(*) FROM items_fts")
    assert cursor.fetchone()[0] == len(sample_items)


def test_store_items_filters_incomplete_data(initialized_db):
    """Test that items with missing name or uniqueName are skipped."""
    raw_data = [
        {"uniqueName": "", "name": "Nameless Item", "category": "Misc", "description": ""},
        {"uniqueName": "/Lotus/Types/NoName", "name": "", "category": "Misc", "description": ""},
        {"uniqueName": "/Lotus/Types/Valid", "name": "Valid Item", "category": "Weapons", "description": "Good"},
    ]

    ingest.store_items(raw_data)

    cursor = initialized_db.cursor()
    cursor.execute("SELECT id, name FROM items")
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0] == ("/Lotus/Types/Valid", "Valid Item")


def test_store_drop_data_inserts_correctly(initialized_db, sample_items):
    """Test that store_drop_data populates both drops and drops_fts tables."""
    drops = [
        {"item": "Alloy Plate", "place": "Earth/Cambria (Spy)", "rarity": "Common", "chance": 25.0},
        {"item": "Excalibur", "place": "War/Assassination", "rarity": "Uncommon", "chance": 10.0},
    ]

    ingest.store_drop_data(drops, items=sample_items)

    cursor = initialized_db.cursor()
    cursor.execute("SELECT count(*) FROM drops")
    assert cursor.fetchone()[0] == 2

    cursor.execute("SELECT count(*) FROM drops_fts")
    assert cursor.fetchone()[0] == 2


def test_store_drop_data_links_item_ids(initialized_db, sample_items):
    """Test that store_drop_data correctly resolves item_id from the items list."""
    # First store items so we have the mapping
    ingest.store_items(sample_items)

    drops = [
        {"item": "Alloy Plate", "place": "Earth/Cambria (Spy)", "rarity": "Common", "chance": 25.0},
        {"item": "Unknown Item", "place": "Somewhere", "rarity": "Rare", "chance": 1.0},
    ]

    ingest.store_drop_data(drops, items=sample_items)

    cursor = initialized_db.cursor()

    # Alloy Plate should have a resolved item_id
    cursor.execute("SELECT item_id FROM drops WHERE item = ?", ("Alloy Plate",))
    row = cursor.fetchone()
    assert row[0] == "/Lotus/Types/Items/MiscItems/AlloyPlate"

    # Unknown Item should have NULL item_id
    cursor.execute("SELECT item_id FROM drops WHERE item = ?", ("Unknown Item",))
    row = cursor.fetchone()
    assert row[0] is None


def test_store_drop_data_filters_incomplete_drops(initialized_db):
    """Test that drops missing item or place are skipped."""
    drops = [
        {"item": "", "place": "Earth/Cambria", "rarity": "Common", "chance": 25.0},
        {"item": "Alloy Plate", "place": "", "rarity": "Common", "chance": 25.0},
        {"item": "Valid Drop", "place": "Valid Place", "rarity": "Common", "chance": 50.0},
    ]

    ingest.store_drop_data(drops)

    cursor = initialized_db.cursor()
    cursor.execute("SELECT count(*) FROM drops")
    assert cursor.fetchone()[0] == 1


def test_store_drop_data_idempotency(initialized_db):
    """Test that running store_drop_data multiple times does not create duplicates."""
    drops = [
        {"item": "Alloy Plate", "place": "Earth/Cambria", "rarity": "Common", "chance": 25.0},
    ]

    ingest.store_drop_data(drops)
    ingest.store_drop_data(drops)

    cursor = initialized_db.cursor()
    cursor.execute("SELECT count(*) FROM drops")
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT count(*) FROM drops_fts")
    assert cursor.fetchone()[0] == 1


def test_main_calls_all_pipeline_steps(temp_db_path):
    """Test that main() invokes init_db, fetch_items, fetch_drop_data, store_items, store_drop_data."""
    with patch("ai_voice_gaming_assistant.data.ingest.init_db") as mock_init, \
         patch("ai_voice_gaming_assistant.data.ingest.fetch_items", return_value=[]) as mock_fetch_items, \
         patch("ai_voice_gaming_assistant.data.ingest.fetch_drop_data", return_value=[]) as mock_fetch_drops, \
         patch("ai_voice_gaming_assistant.data.ingest.store_items") as mock_store_items, \
         patch("ai_voice_gaming_assistant.data.ingest.store_drop_data") as mock_store_drops:
        ingest.main()
        mock_init.assert_called_once()
        mock_fetch_items.assert_called_once()
        mock_fetch_drops.assert_called_once()
        mock_store_items.assert_called_once_with([])
        mock_store_drops.assert_called_once_with([], items=[])
