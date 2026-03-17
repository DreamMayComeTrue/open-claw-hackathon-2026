"""
check_deepgram_tts.py — Verify Deepgram TTS is working
Synthesizes a short phrase and saves it to test_tts_output.mp3

Usage:
    python check_deepgram_tts.py
"""

import os
import urllib.request
import urllib.parse
import json
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
if not DEEPGRAM_API_KEY:
    print("❌ DEEPGRAM_API_KEY not set in .env")
    exit(1)

# TTS model and voice to test — matches agent.py
TTS_MODEL = "aura-2-asteria-en"
TEXT      = "Hey, LongLong here! Deepgram TTS is working perfectly."
OUT_FILE  = "test_tts_output.mp3"

url = f"https://api.deepgram.com/v1/speak?model={TTS_MODEL}"

payload = json.dumps({"text": TEXT}).encode("utf-8")
req = urllib.request.Request(
    url,
    data=payload,
    headers={
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
    },
    method="POST",
)

print(f"🎙️  Synthesizing with model: {TTS_MODEL}")
print(f"   Text: \"{TEXT}\"")

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status == 200:
            audio_data = resp.read()
            with open(OUT_FILE, "wb") as f:
                f.write(audio_data)
            print(f"✅ Audio saved to {OUT_FILE} ({len(audio_data):,} bytes)")
        else:
            print(f"❌ HTTP {resp.status}: {resp.read().decode()}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP {e.code}: {body}")
except Exception as e:
    print(f"❌ Error: {e}")
