"""Client for reading local WFCD JSON from submodules"""

import json
from pathlib import Path
from typing import Any

ITEMS_DIR = Path("data/warframe-items/data/json")
DROPS_DIR = Path("data/warframe-drop-data/data")

EXCLUDED_FILES = {"All.json", "all.slim.json", "i18n.json", "info.json"}

def _read_json_files(directory: Path) -> list[dict[str, Any]]:
    combined_data = []
    if not directory.exists():
        return combined_data
        
    for json_file in directory.glob("*.json"):
        if json_file.name in EXCLUDED_FILES:
            continue
            
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined_data.extend(data)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
            
    return combined_data

def fetch_items() -> list[dict[str, Any]]:
    return _read_json_files(ITEMS_DIR)

def fetch_drop_data() -> list[dict[str, Any]]:
    # The individual files in warframe-drop-data have wildly varying nested schemas.
    # all.slim.json is the pre-flattened version provided by WFCD and is preferrable to use.
    slim_path = DROPS_DIR / "all.slim.json"
    if slim_path.exists():
        try:
            with open(slim_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {slim_path}: {e}")
    return []
