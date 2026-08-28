# Client for fetching pre-parsed WFCD JSON
from typing import Any
import httpx

ITEMS_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/All.json"
DROPS_URL = "https://raw.githubusercontent.com/WFCD/warframe-drop-data/refs/heads/main/data/all.slim.json"

def fetch_items() -> list[dict[str, Any]]:
    response = httpx.get(ITEMS_URL)
    response.raise_for_status()
    return response.json()

def fetch_drop_data() -> list[dict[str, Any]]:
    response = httpx.get(DROPS_URL)
    response.raise_for_status()
    return response.json()
