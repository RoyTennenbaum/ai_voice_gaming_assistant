import json
from pathlib import Path

import pytest

from ai_voice_gaming_assistant.data import wfcd_client


@pytest.fixture
def items_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary items directory and patch wfcd_client to use it."""
    d = tmp_path / "items" / "data" / "json"
    d.mkdir(parents=True)
    monkeypatch.setattr(wfcd_client, "ITEMS_DIR", d)
    return d


@pytest.fixture
def drops_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary drops directory and patch wfcd_client to use it."""
    d = tmp_path / "drops" / "data"
    d.mkdir(parents=True)
    monkeypatch.setattr(wfcd_client, "DROPS_DIR", d)
    return d


def test_fetch_items_reads_multiple_json_files(items_dir: Path):
    """Test that fetch_items combines data from multiple JSON list files."""
    warframes = [{"name": "Excalibur"}, {"name": "Mag"}]
    weapons = [{"name": "Braton"}, {"name": "Lato"}]
    (items_dir / "Warframes.json").write_text(json.dumps(warframes))
    (items_dir / "Weapons.json").write_text(json.dumps(weapons))

    result = wfcd_client.fetch_items()
    names = {item["name"] for item in result}

    assert len(result) == 4
    assert names == {"Excalibur", "Mag", "Braton", "Lato"}


def test_fetch_items_excludes_blocked_files(items_dir: Path):
    """Test that All.json, all.slim.json, i18n.json, and info.json are excluded."""
    valid = [{"name": "Excalibur"}]
    blocked = [{"name": "Should Not Appear"}]

    (items_dir / "Warframes.json").write_text(json.dumps(valid))
    (items_dir / "All.json").write_text(json.dumps(blocked))
    (items_dir / "all.slim.json").write_text(json.dumps(blocked))
    (items_dir / "i18n.json").write_text(json.dumps(blocked))
    (items_dir / "info.json").write_text(json.dumps(blocked))

    result = wfcd_client.fetch_items()

    assert len(result) == 1
    assert result[0]["name"] == "Excalibur"


def test_fetch_items_returns_empty_for_missing_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test that fetch_items returns an empty list when the directory doesn't exist."""
    monkeypatch.setattr(wfcd_client, "ITEMS_DIR", tmp_path / "nonexistent")

    result = wfcd_client.fetch_items()
    assert result == []


def test_fetch_items_skips_dict_json(items_dir: Path):
    """Test that JSON files containing a dict (not a list) are silently skipped."""
    (items_dir / "Warframes.json").write_text(json.dumps([{"name": "Excalibur"}]))
    (items_dir / "SomeConfig.json").write_text(json.dumps({"key": "value"}))

    result = wfcd_client.fetch_items()

    assert len(result) == 1
    assert result[0]["name"] == "Excalibur"


def test_fetch_items_handles_corrupt_json(items_dir: Path):
    """Test that a corrupt JSON file is skipped without crashing."""
    (items_dir / "Warframes.json").write_text(json.dumps([{"name": "Excalibur"}]))
    (items_dir / "Corrupt.json").write_text("{this is not valid json!!!")

    result = wfcd_client.fetch_items()

    assert len(result) == 1
    assert result[0]["name"] == "Excalibur"


def test_fetch_drop_data_reads_slim_json(drops_dir: Path):
    """Test that fetch_drop_data reads from all.slim.json."""
    drops = [{"item": "Braton Prime Barrel", "place": "Lith B1 Relic", "rarity": "Common", "chance": 25.33}]
    (drops_dir / "all.slim.json").write_text(json.dumps(drops))

    result = wfcd_client.fetch_drop_data()

    assert len(result) == 1
    assert result[0]["item"] == "Braton Prime Barrel"


def test_fetch_drop_data_returns_empty_when_missing(drops_dir: Path):
    """Test that fetch_drop_data returns an empty list when all.slim.json is missing."""
    # drops_dir exists but has no all.slim.json
    result = wfcd_client.fetch_drop_data()
    assert result == []
