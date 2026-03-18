# LongLong (龙龙) — LiveKit Desktop Voice Agent  
Open Claw Hackathon 2026 · *Mission Impossible but Try To Be Possible*

LongLong is a Windows-focused, real‑time **voice AI agent** built on **LiveKit (WebRTC)**. It supports **full‑duplex** conversation (you can interrupt mid‑sentence) and can execute local desktop actions such as opening apps/websites, typing, pressing shortcuts, taking screenshots, checking weather/time, and adjusting system volume.

---

## Key Features

- **Low-latency voice** via LiveKit (WebRTC)
- **Full‑duplex** interaction with interruption support
- **Tool calling** for Windows desktop automation (apps, browser, keyboard, volume)
- **Screen understanding** (screenshot capture + vision description, if configured)
- **Desktop packaging** using **PyQt5 + Qt WebEngine** (no browser permission popups)

---

## System Overview (Architecture)

This module is composed of three main parts:

1. **Desktop Shell (`app.py`)**  
   A PyQt5 application that embeds the web UI (`frontend.html`) inside Qt WebEngine. It injects LiveKit credentials into the UI, starts the agent process, and dispatches the agent into the LiveKit room.

2. **Web UI (`frontend.html`)**  
   A LiveKit-enabled HTML/JS client that:
   - publishes microphone audio to the room  
   - plays the agent’s audio output  
   - displays conversation state/transcription

3. **Agent Worker (`agent.py`)**  
   A LiveKit Agents worker that joins the room and runs a voice pipeline:
   - **VAD** (Silero) → speech detection  
   - **STT** (Deepgram) → speech-to-text  
   - **LLM** (Anthropic, via `livekit.plugins.anthropic`) → reasoning + tool selection  
   - **TTS** (Deepgram) → text-to-speech back into the room  

LiveKit acts as the real-time transport layer between UI and agent.

---

## Repository Layout (this folder)

- `agent.py` — LiveKit voice agent + tool definitions
- `frontend.html` — LiveKit web UI (embedded by PyQt or opened in a browser)
- `app.py` — Desktop launcher (PyQt5 window + agent dispatch)
- `launch.py` — Simple launcher (agent + browser UI)
- `requirements.txt` — Python dependencies
- `.env.example` — environment variables template
- `_longlong_ui.html` — generated UI output file (browser fallback / launcher output)

---

## Prerequisites

- Windows 10/11 recommended (desktop automation tools are Windows-oriented)
- Python 3.10+ recommended
- LiveKit project (LiveKit Cloud or self-hosted)
- API keys:
  - **LiveKit**: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
  - **Deepgram**: `DEEPGRAM_API_KEY`
  - **Anthropic**: `ANTHROPIC_API_KEY`

---

## Setup

### 1) Install dependencies

```bash
cd longlong_livekit
pip install -r requirements.txt
python -m livekit.plugins.silero download
```

### 2) Configure environment variables

Create `.env` from the template:

```bash
copy .env.example .env
```

Fill in the values:

```dotenv
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

ANTHROPIC_API_KEY=sk-ant-...
DEEPGRAM_API_KEY=...
```

> Note: `.env.example` includes additional keys (e.g., Groq / ElevenLabs). They may not be required depending on your current `agent.py` configuration.

---

## Running LongLong

### Option A — Desktop App (recommended)

Starts:
- `agent.py` as a background process
- dispatches the agent into the LiveKit room
- opens the UI in a PyQt5 desktop window

```bash
python app.py
```

### Option B — Browser Launcher

Starts the agent and opens the UI in your default browser:

```bash
python launch.py
```

### Option C — Agent Only

Run only the agent worker (useful for debugging or connecting from another LiveKit client):

```bash
python agent.py dev
```

---

## Voice Commands (Examples)

You can speak short natural phrases such as:

- “What time is it?”
- “Weather in Kuala Lumpur.”
- “Open YouTube.”
- “Search the web for Python tutorials.”
- “Close Chrome.”
- “Press Ctrl+L.”
- “Type hello world.”
- “Set volume to 30.”
- “What’s on my screen?”

---

## Troubleshooting

### Anthropic model errors (404 “model not found”)
If you see an error similar to:
`anthropic.NotFoundError ... model: <name>`

The configured model string is not available for your Anthropic API key. Update the model name in `agent.py` (both LLM and screenshot vision calls) to a supported model, and/or configure it via an environment variable.

### No microphone / audio playback
- Ensure Windows microphone permissions allow desktop apps.
- For browser mode, the browser may require a user click before audio playback.
- Desktop mode uses Chromium flags to reduce permission popups.

### Desktop automation limitations
Some tools (volume/app control) are Windows-specific and may require appropriate permissions depending on the environment.

---

## License / Credits

Built for Open Claw Hackathon 2026.  
Powered by LiveKit (WebRTC), Deepgram (STT/TTS), Silero (VAD), and Anthropic (LLM).
