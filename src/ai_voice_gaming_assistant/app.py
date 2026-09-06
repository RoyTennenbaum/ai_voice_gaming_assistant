"""Application entrypoint for the AI Voice Gaming Assistant."""

import asyncio
from ai_voice_gaming_assistant.interface.audio import AudioManager
from ai_voice_gaming_assistant.interface.voice_client import VoiceClient

async def async_main():
    audio_manager = AudioManager()
    voice_client = VoiceClient()

    audio_manager.start()
    try:
        await voice_client.start_session(audio_manager)
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
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
