# 嘿小宝 — Bilingual Voice AI Agent
### Open Claw Hackathon Edition 🏆

A voice-controlled AI agent that understands Chinese and English, controls your
Google Calendar, sends emails, opens websites, reads files, and responds with
natural ElevenLabs streaming voice. Powered by Claude + MediaPipe gestures.

---

## Quick Setup (Windows)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

> If pyaudio fails on Windows:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 2. Set up API keys
```bash
copy .env.example .env
# Edit .env with your keys
```

Keys you need:
| Key | Get it from |
|-----|-------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `DEEPGRAM_API_KEY` | https://console.deepgram.com |
| `ELEVENLABS_API_KEY` | https://elevenlabs.io |
| `ELEVENLABS_VOICE_ID` | https://elevenlabs.io/voice-library |

### 3. Set up Google Calendar & Gmail
1. Go to https://console.cloud.google.com
2. Create a project → Enable **Google Calendar API** and **Gmail API**
3. Create OAuth credentials → Download as `credentials.json`
4. Place `credentials.json` in the project root folder
5. First run will open browser for Google sign-in → creates `token.json`

### 4. Run 小宝
```bash
python main.py
```

---

## Usage — What You Can Say

| Say this | What happens |
|----------|-------------|
| 嘿小宝，明天下午三点帮我创建一个会议 | Creates calendar event tomorrow 3pm |
| 嘿小宝，我今天有什么日程？ | Lists upcoming events |
| Hey Xiaobao, open YouTube | Opens YouTube in browser |
| Hey Xiaobao, search for Python tutorials | Google search |
| 嘿小宝，帮我发邮件给 test@gmail.com | Sends email |
| Hey Xiaobao, read my file at C:/notes.txt | Reads file aloud |
| 嘿小宝，现在几点？ | Tells current time |
| Hey Xiaobao, open Notepad | Opens Windows app |
| Hey Xiaobao, set volume to 50 | Sets system volume |
| Hey Xiaobao, take a screenshot | Saves screenshot to Desktop |

## Gesture Controls (MediaPipe)
| Gesture | Action |
|---------|--------|
| 👍 Thumbs up | Confirm last action |
| 👎 Thumbs down | Cancel |
| ✋ Open palm | Pause listening |
| ✌️ Peace sign | (customisable) |

---

## Project Structure
```
xiaobao/
├── main.py              # Entry point
├── config.py            # API keys from .env
├── requirements.txt
├── credentials.json     # Google OAuth (you add this)
├── agent/
│   ├── wake_word.py     # 嘿小宝 detection
│   ├── stt.py           # Deepgram bilingual STT
│   ├── brain.py         # Claude agent with tool calling
│   ├── tts.py           # ElevenLabs streaming TTS
│   └── vision.py        # MediaPipe gestures
├── tools/
│   ├── calendar_tools.py
│   ├── browser_tools.py
│   ├── email_tools.py
│   ├── file_tools.py
│   └── system_tools.py
└── utils/
    └── display.py       # Coloured terminal output
```
