import sqlite3


def test_fts5_search_by_name(initialized_db, sample_items):
    """Test full-text search matching an item by name."""
    cursor = initialized_db.cursor()

    # Populate items and FTS table
    for item in sample_items:
        cursor.execute(
            "INSERT INTO items (id, name, category, description) VALUES (?, ?, ?, ?)",
            (item["uniqueName"], item["name"], item["category"], item["description"]),
        )
        cursor.execute(
            "INSERT INTO items_fts (name, category, description) VALUES (?, ?, ?)",
            (item["name"], item["category"], item["description"]),
        )
    initialized_db.commit()

    # Search for "Excalibur"
    query = "SELECT name, category FROM items_fts WHERE items_fts MATCH ?"
    results = cursor.execute(query, ("Excalibur",)).fetchall()

    assert len(results) == 1
    assert results[0] == ("Excalibur", "Warframes")


def test_fts5_search_by_description_keyword(initialized_db, sample_items):
    """Test full-text search matching an item by keyword in its description."""
    cursor = initialized_db.cursor()

    for item in sample_items:
        cursor.execute(
            "INSERT INTO items_fts (name, category, description) VALUES (?, ?, ?)",
            (item["name"], item["category"], item["description"]),
        )
    initialized_db.commit()

    # Query for 'razorback' - matches 'Razorback Cipher' (name) and 'Cryptographic ALU' (description: "Used to build Razorback Ciphers.")
    query = "SELECT name, category FROM items_fts WHERE items_fts MATCH ?"
    results = cursor.execute(query, ("razorback",)).fetchall()

    matched_names = {row[0] for row in results}
    assert "Razorback Cipher" in matched_names
    assert "Cryptographic ALU" in matched_names
    assert len(results) == 2


def test_fts5_search_no_match(initialized_db, sample_items):
    """Test full-text search when no records match query."""
    cursor = initialized_db.cursor()

    for item in sample_items:
        cursor.execute(
            "INSERT INTO items_fts (name, category, description) VALUES (?, ?, ?)",
            (item["name"], item["category"], item["description"]),
        )
    initialized_db.commit()

    query = "SELECT name, category FROM items_fts WHERE items_fts MATCH ?"
    results = cursor.execute(query, ("nonexistent_item_query",)).fetchall()

    assert len(results) == 0


def test_fts5_drops_search_by_item_name(initialized_db):
    """Test full-text search on the drops_fts table by item name."""
    cursor = initialized_db.cursor()

    cursor.execute(
        "INSERT INTO drops_fts (item, place, rarity, drop_chance) VALUES (?, ?, ?, ?)",
        ("Braton Prime Barrel", "Lith B1 Relic (Radiant)", "Common", 25.33),
    )
    cursor.execute(
        "INSERT INTO drops_fts (item, place, rarity, drop_chance) VALUES (?, ?, ?, ?)",
        ("Nikana Prime Blueprint", "Axi A1 Relic (Intact)", "Rare", 2.0),
    )
    initialized_db.commit()

    query = "SELECT item, place FROM drops_fts WHERE drops_fts MATCH ?"
    results = cursor.execute(query, ("Braton",)).fetchall()

    assert len(results) == 1
    assert results[0] == ("Braton Prime Barrel", "Lith B1 Relic (Radiant)")
