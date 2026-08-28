# Pipeline script orchestrating database population and vector chunking
from typing import Any

from ai_voice_gaming_assistant.core.db import get_connection, init_db
from ai_voice_gaming_assistant.data.wfcd_client import ALL_ITEMS_URL, fetch_items


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


def fetch_and_store_items() -> None:
    items = fetch_items()
    store_items(items)


def main() -> None:
    init_db()
    fetch_and_store_items()


if __name__ == "__main__":
    main()