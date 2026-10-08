"""Unit tests for audio device checking and AudioManager."""

from unittest.mock import patch, MagicMock
import pytest
import sounddevice as sd

from ai_voice_gaming_assistant.interface.audio import (
    AudioDeviceError,
    get_available_input_devices,
    get_default_input_device,
    resolve_input_device,
    resolve_output_device,
    AudioManager
)

MOCK_DEVICES = [
    {
        'name': 'Speakers (Realtek)',
        'hostapi': 0,
        'max_input_channels': 0,
        'max_output_channels': 2,
        'default_samplerate': 48000.0
    },
    {
        'name': 'Microphone (USB Audio)',
        'hostapi': 0,
        'max_input_channels': 1,
        'max_output_channels': 0,
        'default_samplerate': 16000.0
    },
    {
        'name': 'Headset Mic (Bluetooth)',
        'hostapi': 1,
        'max_input_channels': 2,
        'max_output_channels': 0,
        'default_samplerate': 16000.0
    }
]

MOCK_HOSTAPIS = (
    {'name': 'MME'},
    {'name': 'Windows WASAPI'}
)

def test_get_available_input_devices():
    with patch('sounddevice.query_devices', return_value=MOCK_DEVICES), \
         patch('sounddevice.query_hostapis', return_value=MOCK_HOSTAPIS), \
         patch('ai_voice_gaming_assistant.interface.audio.is_input_device_connected', return_value=True):
        devices = get_available_input_devices()
        assert len(devices) == 2
        assert devices[0]['index'] == 1
        assert 'USB Audio' in devices[0]['name']
        assert devices[1]['index'] == 2
        assert 'Bluetooth' in devices[1]['name']

def test_get_default_input_device_when_none():
    with patch.object(sd.default, 'device', [-1, 0]):
        assert get_default_input_device() is None

def test_get_default_input_device_when_valid():
    with patch.object(sd.default, 'device', [1, 0]), \
         patch('sounddevice.query_devices', return_value=MOCK_DEVICES[1]):
        assert get_default_input_device() == 1

def test_resolve_input_device_by_index():
    with patch('sounddevice.query_devices', return_value=MOCK_DEVICES[1]):
        dev = resolve_input_device(device_preference=1)
        assert dev == 1

def test_resolve_input_device_by_invalid_index():
    with patch('sounddevice.query_devices', side_effect=sd.PortAudioError("Invalid device")):
        with pytest.raises(AudioDeviceError) as exc_info:
            resolve_input_device(device_preference=99)
        assert "Invalid input device index 99" in str(exc_info.value)

def test_resolve_input_device_by_name():
    with patch('sounddevice.query_devices', return_value=MOCK_DEVICES), \
         patch('sounddevice.query_hostapis', return_value=MOCK_HOSTAPIS), \
         patch('ai_voice_gaming_assistant.interface.audio.is_input_device_connected', return_value=True):
        dev = resolve_input_device(device_preference="Bluetooth")
        assert dev == 2

def test_resolve_input_device_no_default_prompts_to_connect_mic():
    with patch.object(sd.default, 'device', [-1, 0]):
        with pytest.raises(AudioDeviceError) as exc_info:
            resolve_input_device(device_preference=None)
        assert "No default or connected microphone detected" in str(exc_info.value)

def test_audio_manager_catches_portaudio_error():
    with patch.object(sd.default, 'device', [1, 0]), \
         patch('sounddevice.query_devices', return_value=MOCK_DEVICES[1]), \
         patch('sounddevice.RawInputStream', side_effect=sd.PortAudioError("Device unavailable")):
        with pytest.raises(AudioDeviceError) as exc_info:
            AudioManager(input_device=1)
        assert "Failed to open microphone stream" in str(exc_info.value)
