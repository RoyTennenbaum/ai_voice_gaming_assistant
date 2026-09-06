"""Voice Client for connecting to Gemini Live API"""

import asyncio
from google import genai
from google.genai import types

from ai_voice_gaming_assistant import config
from ai_voice_gaming_assistant.interface.audio import AudioManager

class VoiceClient:
    """Manages the real-time WebSocket connection to the Gemini Live API."""

    def __init__(self):
        self.client = genai.Client(api_key=config.get_gemini_api_key())
        self.model = config.DEFAULT_LIVE_MODEL
        
    async def start_session(self, audio_manager: AudioManager):
        """Starts a live session, streaming audio bidirectionally."""
        print(f"Connecting to Gemini Live API ({self.model})...")
        
        # Configure system prompt, voice, and enable Google Search
        live_config = types.LiveConnectConfig(
            system_instruction=types.Content(parts=[types.Part.from_text(text=config.SYSTEM_PROMPT)]),
            tools=[types.Tool(google_search=types.GoogleSearchTool())],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=config.VOICE_PERSONA
                    )
                )
            ),
            response_modalities=["AUDIO"]
        )
        
        # Connect to the live API
        async with self.client.aio.live.connect(model=self.model, config=live_config) as session:
            print("Connected! Hold PTT key and start talking.")
            
            # Run send and receive loops concurrently
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._send_loop(session, audio_manager))
                tg.create_task(self._receive_loop(session, audio_manager))

    async def _send_loop(self, session, audio_manager: AudioManager):
        """Reads mic input chunks from the AudioManager and sends them to Gemini."""
        async for chunk in audio_manager.async_mic_stream():
            await session.send(
                input={
                    "realtime_input": {
                        "media_chunks": [
                            {
                                "mime_type": "audio/pcm;rate=16000",
                                "data": chunk
                            }
                        ]
                    }
                }
            )

    async def _receive_loop(self, session, audio_manager: AudioManager):
        """Receives events from Gemini: streams audio out and logs text to console."""
        async for response in session.receive():
            server_content = response.server_content
            if server_content is not None:
                model_turn = server_content.model_turn
                if model_turn is not None:
                    for part in model_turn.parts:
                        # Play back audio chunks
                        if part.inline_data:
                            await audio_manager.play_audio(part.inline_data.data)
                        # Print transcript to console
                        if part.text:
                            print(f"[Cephalon]: {part.text}", end="", flush=True)
                            
                # Note when model is interrupted or finished talking
                if server_content.interrupted:
                    print("\n[Cephalon Interrupted]")
                if server_content.turn_complete:
                    print() # Newline after turn
