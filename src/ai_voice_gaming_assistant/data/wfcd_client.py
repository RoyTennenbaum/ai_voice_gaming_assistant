# Client for fetching pre-parsed WFCD JSON
from typing import Any
import httpx

ALL_ITEMS_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/All.json"


def fetch_items() -> list[dict[str, Any]]:
    response = httpx.get(ALL_ITEMS_URL)
    response.raise_for_status()
    return response.json()
