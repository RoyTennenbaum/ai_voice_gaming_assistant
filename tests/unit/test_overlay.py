"""Unit tests for OverlayHUD widget."""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ai_voice_gaming_assistant.interface.overlay import OverlayHUD


@pytest.fixture(scope="session")
def qapp():
    """Ensure a QApplication instance exists for headless/GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_overlay_initialization(qapp):
    """Test overlay default configuration, size, and window flags."""
    hud = OverlayHUD()
    assert hud.width() == 120
    assert hud.height() == 120
    assert hud._current_state == "IDLE"

    # Check window flags for desktop overlay
    flags = hud.windowFlags()
    assert flags & Qt.WindowType.FramelessWindowHint
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert flags & Qt.WindowType.WindowTransparentForInput
    assert flags & Qt.WindowType.Tool


def test_overlay_state_transitions(qapp):
    """Test switching states updates the internal state and properties."""
    hud = OverlayHUD()

    for state in ["LISTENING", "RETRIEVING", "SPEAKING", "IDLE"]:
        hud.set_state(state)
        assert hud._current_state == state

    # Test invalid state is ignored
    hud.set_state("INVALID_STATE")
    assert hud._current_state == "IDLE"
