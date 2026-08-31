from ai_voice_gaming_assistant.core import db
from ai_voice_gaming_assistant.data import ingest


def test_full_ingest_and_search_flow(temp_db_path, sample_items):
    """Test the complete workflow: init_db -> store_items -> store_drop_data -> search."""
    db.init_db()

    # Ingest items
    ingest.store_items(sample_items)

    # Ingest drops
    drops = [
        {"item": "Alloy Plate", "place": "Earth/Cambria (Spy)", "rarity": "Common", "chance": 25.0},
    ]
    ingest.store_drop_data(drops, items=sample_items)

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

    # Verify drops were ingested with correct item_id linkage
    cursor.execute("SELECT item_id, item, place FROM drops WHERE item = ?", ("Alloy Plate",))
    drop = cursor.fetchone()
    assert drop[0] == "/Lotus/Types/Items/MiscItems/AlloyPlate"
    assert drop[1] == "Alloy Plate"

    conn.close()


def test_ingest_pipeline_idempotency(temp_db_path, sample_items):
    """Test that running the full ingest pipeline multiple times preserves exact search results and row counts."""
    db.init_db()

    # Ingest data twice
    ingest.store_items(sample_items)
    ingest.store_items(sample_items)

    conn = db.get_connection()
    cursor = conn.cursor()

    # FTS Search should only match 1 record for 'armor', not 2
    cursor.execute("SELECT name, category FROM items_fts WHERE items_fts MATCH ?", ("armor",))
    results = cursor.fetchall()
    assert len(results) == 1

    # Verify total count in items and items_fts
    cursor.execute("SELECT count(*) FROM items")
    assert cursor.fetchone()[0] == len(sample_items)

    cursor.execute("SELECT count(*) FROM items_fts")
    assert cursor.fetchone()[0] == len(sample_items)

    conn.close()
