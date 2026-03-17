# config.py
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
DEEPGRAM_API_KEY     = os.getenv("DEEPGRAM_API_KEY", "")
ELEVENLABS_API_KEY   = os.getenv("ELEVENLABS_API_KEY", "")

# ElevenLabs voice ID — "Rachel" is natural, supports Chinese well
# Find more at: https://elevenlabs.io/voice-library
# For Chinese, consider "Aria" or a custom cloned voice
ELEVENLABS_VOICE_ID  = os.getenv("ELEVENLABS_VOICE_ID", "FGY2WhTYpPnrIDTdsKH5")
