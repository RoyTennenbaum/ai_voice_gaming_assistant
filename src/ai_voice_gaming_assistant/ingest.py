from ai_voice_gaming_assistant.db import get_connection, init_db
import httpx

ALL_ITEMS_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/All.json"

def fetch_and_store_items() -> None:
    response = httpx.get(ALL_ITEMS_URL)

    response.raise_for_status()

    items = response.json()

    conn = get_connection()
    cursor = conn.cursor()

    for item in items:
        item_id = item.get("uniqueName", "")
        name = item.get("name", "")
        category = item.get("category", "")
        description = item.get("description", "")

        if name and item_id:
            cursor.execute(
                """
                INSERT OR REPLACE INTO items (id, name, category, description)
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

def main() -> None:
    init_db()
    fetch_and_store_items()

if __name__ == "__main__":
    main()