"""Audio I/O"""

import sys
import asyncio
import sounddevice as sd
from pynput import keyboard

from ai_voice_gaming_assistant.config import (
    AUDIO_INPUT_SAMPLE_RATE,
    AUDIO_OUTPUT_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    AUDIO_INPUT_DEVICE,
    AUDIO_OUTPUT_DEVICE,
    PTT_KEY
)

class AudioDeviceError(RuntimeError):
    """Raised when an audio input or output device is missing or cannot be opened."""
    pass

def is_input_device_connected(index: int, dev: dict, api_name: str) -> bool:
    """Verifies if an audio device is physically connected and can open a stream."""
    if dev.get('max_input_channels', 0) <= 0:
        return False
    # On Windows, WDM-KS driver handles keep phantom entries for disconnected devices.
    # We probe the device with a lightweight stream test to verify connectivity.
    try:
        sr = int(dev.get('default_samplerate', 16000))
        test_stream = sd.RawInputStream(
            samplerate=sr,
            channels=1,
            device=index,
            callback=lambda *args: None
        )
        test_stream.start()
        test_stream.stop()
        test_stream.close()
        return True
    except Exception:
        return False

def get_available_input_devices(only_connected: bool = True) -> list[dict]:
    """Returns a list of all audio input devices detected on the system."""
    devices = []
    try:
        hostapis = sd.query_hostapis()
        for idx, dev in enumerate(sd.query_devices()):
            if dev.get('max_input_channels', 0) > 0:
                api_name = hostapis[dev['hostapi']]['name'] if 'hostapi' in dev else "Unknown API"
                if only_connected and not is_input_device_connected(idx, dev, api_name):
                    continue
                clean_name = " ".join(dev['name'].split())
                devices.append({
                    'index': idx,
                    'name': clean_name,
                    'channels': dev['max_input_channels'],
                    'hostapi': api_name,
                    'default_samplerate': dev.get('default_samplerate', 0),
                })
    except Exception as e:
        print(f"Warning: Failed to query audio devices: {e}")
    return devices

def get_default_input_device() -> int | None:
    """Returns the index of the default input device if valid, otherwise None."""
    try:
        def_idx = sd.default.device[0]
        if def_idx is not None and def_idx != -1:
            info = sd.query_devices(def_idx)
            if info.get('max_input_channels', 0) > 0:
                return def_idx
    except Exception:
        pass
    return None

def resolve_input_device(device_preference=None, interactive: bool = True) -> int | None:
    """Resolves which input device to use, prompting the user if no microphone or default exists."""
    # 1. Explicit preference specified (via argument or AUDIO_INPUT_DEVICE config)
    if device_preference is not None:
        if isinstance(device_preference, str) and device_preference.strip().isdigit():
            device_preference = int(device_preference.strip())

        if isinstance(device_preference, int):
            try:
                info = sd.query_devices(device_preference)
                if info.get('max_input_channels', 0) <= 0:
                    raise AudioDeviceError(
                        f"Specified audio device [{device_preference}] '{info.get('name')}' "
                        f"has no input channels."
                    )
                return device_preference
            except Exception as e:
                raise AudioDeviceError(f"Invalid input device index {device_preference}: {e}") from None
        elif isinstance(device_preference, str):
            query = device_preference.strip().lower()
            available = get_available_input_devices(only_connected=True)
            matched = [d for d in available if query in d['name'].lower()]
            if matched:
                return matched[0]['index']
            available_names = [d['name'] for d in available]
            raise AudioDeviceError(
                f"No connected input device matching '{device_preference}' found. "
                f"Available devices: {available_names}"
            )

    # 2. Check if the system has a valid default input device
    default_dev = get_default_input_device()
    if default_dev is not None:
        return default_dev

    # 3. No default microphone or no connected device found
    print("\n" + "=" * 65)
    print("No microphone detected!")
    print("Please connect a microphone or headset and restart the assistant.")
    print("\n\nMore Detailed Troubleshooting:")
    print("  1. Connect a USB microphone, 3.5mm mic, or Bluetooth headset.")
    print("  2. In Windows Settings -> System -> Sound:")
    print("     Ensure your microphone is detected and set as Default.")
    print("  3. In Windows Settings -> Privacy & security -> Microphone:")
    print("     Ensure 'Microphone access' and desktop apps are allowed.")
    print("=" * 65 + "\n")
    raise AudioDeviceError(
        "No default or connected microphone detected. Please connect a microphone."
    )

def resolve_output_device(device_preference=None) -> int | None:
    """Resolves output device preference if specified."""
    if device_preference is None:
        return None
    if isinstance(device_preference, str) and device_preference.strip().isdigit():
        device_preference = int(device_preference.strip())
    if isinstance(device_preference, int):
        return device_preference
    if isinstance(device_preference, str):
        query = device_preference.strip().lower()
        try:
            for idx, dev in enumerate(sd.query_devices()):
                if dev.get('max_output_channels', 0) > 0 and query in dev['name'].lower():
                    return idx
        except Exception:
            pass
    return None

class AudioManager:
    """Manages audio capture (mic) and playback (speaker) with Push-to-Talk functionality."""

    def __init__(self, input_device=None, output_device=None, interactive: bool = True):
        self.input_queue = asyncio.Queue()
        self.is_recording = False
        self._loop = None
        
        # Resolve devices
        self.input_device = resolve_input_device(
            input_device if input_device is not None else AUDIO_INPUT_DEVICE,
            interactive=interactive
        )
        self.output_device = resolve_output_device(
            output_device if output_device is not None else AUDIO_OUTPUT_DEVICE
        )

        # Configure the input stream with a callback to push audio data to our queue
        try:
            self.in_stream = sd.RawInputStream(
                samplerate=AUDIO_INPUT_SAMPLE_RATE,
                channels=AUDIO_CHANNELS,
                dtype='int16',
                blocksize=AUDIO_CHUNK_SIZE,
                device=self.input_device,
                callback=self._input_callback
            )
        except (sd.PortAudioError, Exception) as e:
            dev_desc = f"device [{self.input_device}]" if self.input_device is not None else "default input device"
            msg = (
                f"Failed to open microphone stream on {dev_desc}: {e}.\n"
                "Please verify the microphone is connected, or select a different device."
            )
            print(f"\n[Audio Error] {msg}\n")
            raise AudioDeviceError(msg) from None
        
        # Configure output stream (no callback, we will write to it synchronously from a background thread)
        try:
            self.out_stream = sd.RawOutputStream(
                samplerate=AUDIO_OUTPUT_SAMPLE_RATE,
                channels=AUDIO_CHANNELS,
                dtype='int16',
                device=self.output_device
            )
        except (sd.PortAudioError, Exception) as e:
            dev_desc = f"device [{self.output_device}]" if self.output_device is not None else "default output device"
            msg = f"Failed to open audio output stream on {dev_desc}: {e}."
            print(f"\n[Audio Error] {msg}\n")
            raise AudioDeviceError(msg) from None
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )

    def start(self):
        """Starts the audio streams and PTT keyboard listener."""
        self._loop = asyncio.get_running_loop()
        try:
            self.in_stream.start()
        except (sd.PortAudioError, Exception) as e:
            raise AudioDeviceError(f"Failed to start microphone stream: {e}") from None
            
        try:
            self.out_stream.start()
        except (sd.PortAudioError, Exception) as e:
            raise AudioDeviceError(f"Failed to start output stream: {e}") from None

        self.listener.start()
        print(f"AudioManager started. Hold '{PTT_KEY}' to talk.")

    def stop(self):
        """Stops streams and listener."""
        if hasattr(self, 'in_stream') and self.in_stream:
            try:
                self.in_stream.stop()
                self.in_stream.close()
            except Exception:
                pass
        if hasattr(self, 'out_stream') and self.out_stream:
            try:
                self.out_stream.stop()
                self.out_stream.close()
            except Exception:
                pass
        if hasattr(self, 'listener') and self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass

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
