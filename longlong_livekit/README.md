# 龙龙 — LiveKit Edition 🐉
### Phone-call quality voice AI · Open Claw Hackathon 2026

Full-duplex voice conversation — interrupt 龙龙 mid-sentence, ~300ms response time.
Stack: Deepgram STT → Groq LLaMA-3.3-70b → ElevenLabs TTS · WebRTC via LiveKit

## Setup (5 minutes)

### 1. Install
```bash
pip install -r requirements.txt
python -m livekit.plugins.silero download    # download VAD model
```

### 2. Get LiveKit credentials (free)
1. Sign up at https://cloud.livekit.io (free tier available)
2. Create a project → copy URL, API Key, API Secret
3. Paste into .env

### 3. Configure .env
```bash
copy .env.example .env
# fill in all keys
```

### 4. Run the agent
```bash
python agent.py dev
```

### 5. Connect your mic
Open the LiveKit Agents Playground to talk to 龙龙:
https://agents-playground.livekit.io

Or use the LiveKit CLI:
```bash
pip install livekit-cli
lk token create --room test --identity user
```

## What you can say
- 现在几点？ / What time is it?
- 帮我打开 YouTube / Open YouTube
- Search for Python tutorials
- 关掉 Chrome / Close Chrome
- 我的屏幕上有什么？/ What's on my screen?
- 帮我按 Ctrl+C / Press Ctrl+C
- 调低音量到 30 / Set volume to 30
- 帮我读这个文件 C:/notes.txt

## Why LiveKit is better than the old approach
| Feature | Old approach | LiveKit |
|---------|-------------|---------|
| Response time | ~2s | ~300ms |
| Interruptions | ❌ Must wait | ✅ Cut off anytime |
| Audio quality | pyaudio (basic) | WebRTC (phone call) |
| Noise cancellation | ❌ | ✅ Built-in |
| Turn detection | Simple silence | Smart VAD + semantic |
| Concurrency | Single thread | Production-grade |
