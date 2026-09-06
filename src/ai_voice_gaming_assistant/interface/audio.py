"""Audio I/O"""

import asyncio
import sounddevice as sd
from pynput import keyboard

from ai_voice_gaming_assistant.config import (
    AUDIO_INPUT_SAMPLE_RATE,
    AUDIO_OUTPUT_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    PTT_KEY
)

class AudioManager:
    """Manages audio capture (mic) and playback (speaker) with Push-to-Talk functionality."""

    def __init__(self):
        self.input_queue = asyncio.Queue()
        self.is_recording = False
        self._loop = None
        
        # Configure the input stream with a callback to push audio data to our queue
        self.in_stream = sd.RawInputStream(
            samplerate=AUDIO_INPUT_SAMPLE_RATE,
            channels=AUDIO_CHANNELS,
            dtype='int16',
            blocksize=AUDIO_CHUNK_SIZE,
            callback=self._input_callback
        )
        
        # Configure output stream (no callback, we will write to it synchronously from a background thread)
        self.out_stream = sd.RawOutputStream(
            samplerate=AUDIO_OUTPUT_SAMPLE_RATE,
            channels=AUDIO_CHANNELS,
            dtype='int16'
        )
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )

    def start(self):
        """Starts the audio streams and PTT keyboard listener."""
        self._loop = asyncio.get_running_loop()
        self.in_stream.start()
        self.out_stream.start()
        self.listener.start()
        print(f"AudioManager started. Hold '{PTT_KEY}' to talk.")

    def stop(self):
        """Stops streams and listener."""
        self.in_stream.stop()
        self.in_stream.close()
        self.out_stream.stop()
        self.out_stream.close()
        self.listener.stop()

    def _input_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio block from the microphone."""
        if status:
            print(f"Audio input warning: {status}")
            
        if self.is_recording and self._loop:
            # Put raw bytes into the queue thread-safely
            self._loop.call_soon_threadsafe(self.input_queue.put_nowait, bytes(indata))

    def _get_key_name(self, key) -> str:
        """Helper to extract the string name of a pynput key."""
        if hasattr(key, 'name') and key.name:
            return key.name
        if hasattr(key, 'char') and key.char:
            return key.char
        return str(key)

    def _on_press(self, key):
        if self._get_key_name(key) == PTT_KEY:
            if not self.is_recording:
                print(f"[{PTT_KEY}] PTT Active: Recording...")
                self.is_recording = True

    def _on_release(self, key):
        if self._get_key_name(key) == PTT_KEY:
            if self.is_recording:
                print(f"[{PTT_KEY}] PTT Released: Stopped recording.")
                self.is_recording = False
                if self._loop:
                    self._loop.call_soon_threadsafe(self.input_queue.put_nowait, None)

    async def async_mic_stream(self):
        """Async generator that yields audio chunks when PTT is active."""
        while True:
            chunk = await self.input_queue.get()
            yield chunk

    async def play_audio(self, pcm_data: bytes):
        """Writes PCM audio data to the speaker output."""
        if pcm_data:
            # Write to the stream in a separate thread so it blocks until audio plays, 
            # providing backpressure without blocking the asyncio event loop.
            await asyncio.to_thread(self.out_stream.write, pcm_data)
