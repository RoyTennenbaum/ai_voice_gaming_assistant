"""Central module for paths, environment variables, models, audio settings, and persona instructions."""

import os
from dotenv import load_dotenv
from pathlib import Path

# ==============================================================================
# Paths & Environment
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

# Database path with environment override option
DB_PATH = Path(os.getenv("WARFRAME_DB_PATH", PROJECT_ROOT / "warframe.db"))

# ==============================================================================
# API Keys & Authentication
# ==============================================================================
def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Please set the GEMINI_API_KEY environment variable "
            "or create a .env file in the project root."
        )
    return key

# ==============================================================================
# Model & Voice Persona Identifiers
# ==============================================================================
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

DEFAULT_LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview")
VOICE_PERSONA = os.getenv("VOICE_PERSONA", "Gacrux")

# ==============================================================================
# Audio & Push-to-Talk (PTT) Specifications
# ==============================================================================
AUDIO_INPUT_SAMPLE_RATE = 16000   # 16kHz PCM mono for microphone capture
AUDIO_OUTPUT_SAMPLE_RATE = 24000  # 24kHz PCM mono for Gemini Live audio playback
AUDIO_CHANNELS = 1                # Mono
AUDIO_CHUNK_SIZE = 1024           # Samples per audio chunk
PTT_KEY = os.getenv("PTT_KEY", "ctrl_r")  # Push-to-Talk activation hotkey

# ==============================================================================
# Q&A Model System Prompt
# ==============================================================================
SYSTEM_PROMPT = """You are a Tactical Cephalon co-pilot assisting a Warframe player in real-time during gameplay.

Core Directives:
- Provide immediate, ultra-concise, high-signal answers to game knowledge queries (item drops, farming locations, relic rewards, mission rotations).
- Avoid conversational filler, lengthy pleasantries, or preamble. Give actionable tactical callouts.
- When reporting drop sources, name the best planet/node, mission type, rotation (A/B/C), and drop percentage.
- When calling tools, use returned data precisely. Highlight the top 2-3 highest probability spots.
- If executing context fallbacks or database tool lookups, emit brief verbal fillers ('Checking...') to mask retrieval latency.
"""