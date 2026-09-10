"""Visual standalone runner for testing the OverlayHUD widget."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from ai_voice_gaming_assistant.interface.overlay import OverlayHUD


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    hud = OverlayHUD()

    # Position in bottom center, 5px from bottom border
    screen_geometry = app.primaryScreen().availableGeometry()
    x = screen_geometry.x() + (screen_geometry.width() - hud.width()) // 2
    y = screen_geometry.y() + screen_geometry.height() - hud.height() - 5
    hud.move(x, y)

    hud.show()

    # Cycle through states every 3 seconds
    states = ["IDLE", "LISTENING", "RETRIEVING", "SPEAKING"]
    current_index = 0

    def cycle_state():
        nonlocal current_index
        current_index = (current_index + 1) % len(states)
        next_state = states[current_index]
        print(f"Switching state to: {next_state}")
        hud.set_state(next_state)

    timer = QTimer()
    timer.timeout.connect(cycle_state)
    timer.start(3000)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
