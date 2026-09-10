"""Voice Client for connecting to Gemini Live API"""

import asyncio
from google import genai
from google.genai import types

from ai_voice_gaming_assistant import config
from ai_voice_gaming_assistant.interface.audio import AudioManager
from ai_voice_gaming_assistant.interface.overlay import OverlayHUD

class VoiceClient:
    """Manages the real-time WebSocket connection to the Gemini Live API."""

    def __init__(self):
        self.client = genai.Client(api_key=config.get_gemini_api_key())
        self.model = config.DEFAULT_LIVE_MODEL
        
    async def start_session(self, audio_manager: AudioManager, hud: OverlayHUD):
        """Starts a live session, streaming audio bidirectionally."""
        print(f"Connecting to Gemini Live API ({self.model})...")
        
        # Configure system prompt, voice, and enable Google Search
        live_config = types.LiveConnectConfig(
            system_instruction=types.Content(parts=[types.Part.from_text(text=config.SYSTEM_PROMPT)]),
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
                tg.create_task(self._send_loop(session, audio_manager, hud))
                tg.create_task(self._receive_loop(session, audio_manager, hud))

    async def _send_loop(self, session, audio_manager: AudioManager, hud: OverlayHUD):
        """Reads mic input chunks from the AudioManager and sends them to Gemini."""
        async for chunk in audio_manager.async_mic_stream():
            if chunk is None:
                hud.set_state("IDLE")
                await session.send_realtime_input(audio_stream_end=True)
            else:
                hud.set_state("LISTENING")
                await session.send_realtime_input(
                    audio=types.Blob(
                        data=chunk,
                        mime_type=f"audio/pcm;rate={config.AUDIO_INPUT_SAMPLE_RATE}"
                    )
                )

    async def _receive_loop(self, session, audio_manager: AudioManager, hud: OverlayHUD):
        """Receives events from Gemini: streams audio out and logs text to console."""
        while True:
            has_message = False
            async for response in session.receive():
                has_message = True
                server_content = response.server_content
                if server_content is not None:
                    model_turn = server_content.model_turn
                    if model_turn is not None:
                        for part in model_turn.parts:
                            # Play back audio chunks
                            if part.inline_data:
                                hud.set_state("SPEAKING")
                                await audio_manager.play_audio(part.inline_data.data)
                            # Print transcript to console
                            if part.text:
                                print(f"[Cephalon]: {part.text}", end="", flush=True)
                            # Check for function/tool call (retrieval)
                            if part.function_call or part.executable_code:
                                hud.set_state("RETRIEVING")
                                
                    # Note when model is interrupted or finished talking
                    if server_content.interrupted:
                        print("\n[Cephalon Interrupted]")
                        hud.set_state("IDLE")
                    if server_content.turn_complete:
                        print() # Newline after turn
                        hud.set_state("IDLE")
            if not has_message:
                break
