# Pipeline script orchestrating database population and vector chunking
from typing import Any

from ai_voice_gaming_assistant.core.db import get_connection, init_db
from ai_voice_gaming_assistant.data.wfcd_client import fetch_items, fetch_drop_data


def store_items(items: list[dict[str, Any]]) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM items")
    cursor.execute("DELETE FROM items_fts")

    for item in items:
        item_id = item.get("uniqueName", "")
        name = item.get("name", "")
        category = item.get("category", "")
        description = item.get("description", "")

        if name and item_id:
            cursor.execute(
                """
                INSERT INTO items (id, name, category, description)
                VALUES (?, ?, ?, ?)
                """,
                (item_id, name, category, description),
            )

            cursor.execute(
                """
                INSERT INTO items_fts (name, category, description)
                VALUES (?, ?, ?)
                """,
                (name, category, description),
            )

    conn.commit()
    conn.close()

def store_drop_data(drops: list[dict[str, Any]], items: list[dict[str, Any]] | None = None) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    name_to_id: dict[str, str] = {}
    if items:
        for item in items:
            name = item.get("name")
            uid = item.get("uniqueName")
            if name and uid and name not in name_to_id:
                name_to_id[name] = uid

    cursor.execute("DELETE FROM drops")
    cursor.execute("DELETE FROM drops_fts")

    for drop in drops:
        item = drop.get("item", "")
        place = drop.get("place", "")
        rarity = drop.get("rarity", "")
        chance = drop.get("chance", "")
        item_id = name_to_id.get(item)

        if item and place:
            cursor.execute(
                """
                INSERT INTO drops (item_id, item, place, rarity, drop_chance)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item_id, item, place, rarity, chance),
            )

            cursor.execute(
                """
                INSERT INTO drops_fts (item, place, rarity, drop_chance)
                VALUES (?, ?, ?, ?)
                """,
                (item, place, rarity, chance),
            )

    conn.commit()
    conn.close()

def fetch_and_store_items() -> None:
    items = fetch_items()
    store_items(items)


def main() -> None:
    init_db()
    items = fetch_items()
    drops = fetch_drop_data()
    store_items(items)
    store_drop_data(drops, items=items)


if __name__ == "__main__":
    main()