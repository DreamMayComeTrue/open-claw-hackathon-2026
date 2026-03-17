"""
龙龙 API Debug Script
Run this to check if all your API keys are loading and working correctly.
python debug_apis.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("\n========== 龙龙 API DEBUG ==========\n")

# ── 1. Check .env is loading ──────────────────────────
ANTHROPIC_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
DEEPGRAM_KEY     = os.getenv("DEEPGRAM_API_KEY", "")
ELEVENLABS_KEY   = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE = os.getenv("ELEVENLABS_VOICE_ID", "")

print("── .env values loaded ──")
print(f"ANTHROPIC_API_KEY   : {'✅ ' + ANTHROPIC_KEY[:12] + '...' if ANTHROPIC_KEY else '❌ MISSING'}")
print(f"DEEPGRAM_API_KEY    : {'✅ ' + DEEPGRAM_KEY[:12] + '...' if DEEPGRAM_KEY else '❌ MISSING'}")
print(f"ELEVENLABS_API_KEY  : {'✅ ' + ELEVENLABS_KEY[:12] + '...' if ELEVENLABS_KEY else '❌ MISSING'}")
print(f"ELEVENLABS_VOICE_ID : {'✅ ' + ELEVENLABS_VOICE if ELEVENLABS_VOICE else '❌ MISSING'}")
print()

# ── 2. Test Deepgram ──────────────────────────────────
print("── Testing Deepgram ──")
try:
    import requests
    # Use a tiny silent WAV (44 bytes) just to test auth
    import wave, io, struct
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(struct.pack('<h', 0) * 160)  # 10ms silence
    buf.seek(0)

    resp = requests.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": "nova-2", "language": "en"},
        headers={
            "Authorization": f"Token {DEEPGRAM_KEY}",
            "Content-Type": "audio/wav",
        },
        data=buf.read(),
        timeout=10,
    )
    if resp.status_code == 200:
        print("✅ Deepgram auth OK — key is valid!")
    elif resp.status_code == 401:
        print(f"❌ Deepgram 401 — Invalid API key. Check your .env")
        print(f"   Response: {resp.text[:200]}")
    elif resp.status_code == 400:
        print(f"⚠️  Deepgram 400 Bad Request — key valid but request issue")
        print(f"   Response: {resp.text[:200]}")
    else:
        print(f"⚠️  Deepgram returned {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"❌ Deepgram connection error: {e}")
print()

# ── 3. Test ElevenLabs ────────────────────────────────
print("── Testing ElevenLabs ──")
try:
    resp = requests.get(
        "https://api.elevenlabs.io/v1/user",
        headers={"xi-api-key": ELEVENLABS_KEY},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        tier = data.get("subscription", {}).get("tier", "unknown")
        chars_left = data.get("subscription", {}).get("character_count", "?")
        chars_limit = data.get("subscription", {}).get("character_limit", "?")
        print(f"✅ ElevenLabs auth OK!")
        print(f"   Plan: {tier}")
        print(f"   Characters used: {chars_left} / {chars_limit}")
    elif resp.status_code == 401:
        print(f"❌ ElevenLabs 401 — Invalid API key. Check your .env")
    else:
        print(f"⚠️  ElevenLabs returned {resp.status_code}: {resp.text[:200]}")
except Exception as e:
    print(f"❌ ElevenLabs connection error: {e}")
print()

# ── 4. Test ElevenLabs Voice ID ───────────────────────
print("── Testing ElevenLabs Voice ID ──")
try:
    resp = requests.get(
        f"https://api.elevenlabs.io/v1/voices/{ELEVENLABS_VOICE}",
        headers={"xi-api-key": ELEVENLABS_KEY},
        timeout=10,
    )
    if resp.status_code == 200:
        name = resp.json().get("name", "unknown")
        print(f"✅ Voice ID valid — voice name: '{name}'")
    elif resp.status_code == 404:
        print(f"❌ Voice ID '{ELEVENLABS_VOICE}' not found on your account!")
        print(f"   → Go to elevenlabs.io → My Voices → copy a valid Voice ID")
    else:
        print(f"⚠️  Voice check returned {resp.status_code}: {resp.text[:200]}")
except Exception as e:
    print(f"❌ Voice ID check error: {e}")
print()

# ── 5. List your available ElevenLabs voices ──────────
print("── Your available ElevenLabs voices ──")
try:
    resp = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": ELEVENLABS_KEY},
        timeout=10,
    )
    if resp.status_code == 200:
        voices = resp.json().get("voices", [])
        if voices:
            for v in voices[:10]:
                print(f"   • {v['name']:<25} ID: {v['voice_id']}")
            print(f"\n   → Copy one of these IDs into your .env as ELEVENLABS_VOICE_ID")
        else:
            print("   No voices found — add a voice at elevenlabs.io/voice-library first")
    else:
        print(f"   Could not fetch voices: {resp.status_code}")
except Exception as e:
    print(f"   Error fetching voices: {e}")

print("\n=====================================\n")
