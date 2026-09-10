"""Application entrypoint for the AI Voice Gaming Assistant."""

import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication

from ai_voice_gaming_assistant.interface.audio import AudioManager
from ai_voice_gaming_assistant.interface.voice_client import VoiceClient
from ai_voice_gaming_assistant.interface.overlay import OverlayHUD

async def async_main(hud: OverlayHUD):
    audio_manager = AudioManager()
    voice_client = VoiceClient()

    audio_manager.start()
    try:
        await voice_client.start_session(audio_manager, hud)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        import traceback
        print(f"Error in voice session: {e}")
        traceback.print_exc()
    finally:
        audio_manager.stop()
        print("Voice session ended.")

def main():
    app = QApplication(sys.argv)
    
    # Initialize HUD
    hud = OverlayHUD()
    # Position in bottom center, 5px from bottom border
    screen_geometry = app.primaryScreen().availableGeometry()
    x = screen_geometry.x() + (screen_geometry.width() - hud.width()) // 2
    y = screen_geometry.y() + screen_geometry.height() - hud.height() - 5
    hud.move(x, y)
    hud.show()
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(async_main(hud))
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
