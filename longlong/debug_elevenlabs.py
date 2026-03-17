"""
ElevenLabs specific debug — tests TTS directly
python debug_elevenlabs.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

KEY      = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

print(f"\nKey loaded  : {KEY[:8]}...{KEY[-4:] if len(KEY) > 12 else '(too short)'}")
print(f"Voice ID    : {VOICE_ID}")
print()

# Test 1: list voices (confirms key works)
print("── Test 1: List voices ──")
r = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": KEY})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ Key is valid!")
else:
    print(f"❌ {r.text[:200]}")
print()

# Test 2: try TTS with correct model for free tier
print("── Test 2: TTS with eleven_monolingual_v1 (free tier model) ──")
r2 = requests.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
    headers={"xi-api-key": KEY, "Content-Type": "application/json"},
    json={
        "text": "Hello, I am LongLong!",
        "model_id": "eleven_monolingual_v1",   # free tier model
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    },
    timeout=15,
)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    print("✅ TTS works with eleven_monolingual_v1!")
else:
    print(f"Response: {r2.text[:300]}")
print()

# Test 3: try turbo model
print("── Test 3: TTS with eleven_turbo_v2_5 ──")
r3 = requests.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
    headers={"xi-api-key": KEY, "Content-Type": "application/json"},
    json={
        "text": "Hello, I am LongLong!",
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    },
    timeout=15,
)
print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    print("✅ TTS works with eleven_turbo_v2_5!")
else:
    print(f"Response: {r3.text[:300]}")
print()

# Test 4: check which models are available
print("── Test 4: Available models on your account ──")
r4 = requests.get("https://api.elevenlabs.io/v1/models", headers={"xi-api-key": KEY})
if r4.status_code == 200:
    for m in r4.json():
        print(f"  • {m['model_id']} — {m.get('name','')}")
else:
    print(f"Could not fetch models: {r4.status_code}")
