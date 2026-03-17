"""
龙龙 — LiveKit Voice Agent
Phone-call quality conversation: full-duplex, interruptible, ~300ms response
Stack: Deepgram STT (multilingual) → Anthropic Claude Sonnet LLM → Deepgram TTS · WebRTC via LiveKit
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import deepgram, silero, anthropic as lk_anthropic
from livekit.plugins import noise_cancellation

load_dotenv()
logger = logging.getLogger("longlong")

# ── System prompt ──────────────────────────────────────────────────────────────

INSTRUCTIONS = """
You are LongLong (龙龙), a smart and capable AI voice assistant built for Open Claw Hackathon 2026.
You are bilingual — respond in whichever language the user speaks (Chinese or English).

PERSONALITY:
- Warm, confident, a little playful — like a helpful friend on a phone call.
- Keep replies SHORT — max 1-2 sentences. This is live voice, not text.
- No markdown, no bullet points, no lists. Speak naturally.
- When you complete a task, confirm it briefly and naturally.
- If unsure, ask one short clarifying question.
- When the user speaks Chinese, reply in Chinese. When they speak English, reply in English.

TOOL USE STRATEGY:
- Always use the most specific tool available for a task. Do not guess — use tools to get real data.
- Chain tools when needed: e.g. take a screenshot THEN describe it to answer questions about the screen.
- Before closing an app, you may list running apps first to confirm it is actually running.
- Prefer shell commands for information queries (dir, ipconfig, systeminfo) over guessing.
- When asked to write or edit a file, always use write_file. Never fabricate file content.

CAPABILITIES:
- Open/close apps and websites
- Control mouse (click) and keyboard (type, shortcuts)
- Take screenshots and describe screen content using vision AI
- Check weather and time
- Read and write files
- Control system volume
- List running processes
- Run safe shell commands
"""

# ── Tools ──────────────────────────────────────────────────────────────────────

@function_tool
async def get_weather(context: RunContext, city: str) -> str:
    """Get current weather for a city."""
    import urllib.request, urllib.parse, json
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        return f"{city} is currently {desc}, {temp_c}°C, humidity {humidity}%"
    except Exception as e:
        return f"Could not get weather for {city}: {e}"


@function_tool
async def get_current_time(context: RunContext) -> str:
    """Get the current date and time."""
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p, %A %B %d")


@function_tool
async def open_website(context: RunContext, url: str) -> str:
    """Open a website in the browser and bring it to the front."""
    import subprocess, webbrowser
    if not url.startswith("http"):
        url = "https://" + url
    # Use start command — opens in foreground on Windows
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"Opened {url}"


@function_tool
async def search_web(context: RunContext, query: str) -> str:
    """Search Google for something."""
    import subprocess, urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"Searching for: {query}"


@function_tool
async def open_application(context: RunContext, app_name: str) -> str:
    """Open a Windows application like notepad, chrome, powershell, spotify, calculator."""
    import subprocess, os
    name = app_name.lower().strip()

    # Use full paths for browsers — avoids 'not recognized' error
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    if name in ["chrome", "google chrome"]:
        for path in chrome_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                return "Opened Chrome"
        # fallback
        subprocess.Popen('start chrome', shell=True)
        return "Opened Chrome"

    if name in ["edge", "microsoft edge"]:
        for path in edge_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                return "Opened Edge"
        subprocess.Popen('start msedge', shell=True)
        return "Opened Edge"

    app_map = {
        "notepad":        "notepad.exe",
        "calculator":     "calc.exe",
        "paint":          "mspaint.exe",
        "explorer":       "explorer.exe",
        "file explorer":  "explorer.exe",
        "powershell":     "powershell.exe",
        "cmd":            "cmd.exe",
        "command prompt": "cmd.exe",
        "vscode":         "code",
        "vs code":        "code",
        "spotify":        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    }

    exe = app_map.get(name, app_name)
    try:
        subprocess.Popen(exe, shell=True)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Could not open {app_name}: {e}"


@function_tool
async def close_application(context: RunContext, app_name: str) -> str:
    """Force close a Windows application."""
    import subprocess
    exe_map = {
        "chrome":         "chrome.exe",
        "google chrome":  "chrome.exe",
        "edge":           "msedge.exe",
        "firefox":        "firefox.exe",
        "notepad":        "notepad.exe",
        "spotify":        "Spotify.exe",
        "vscode":         "Code.exe",
        "vs code":        "Code.exe",
        "powershell":     "powershell.exe",
        "cmd":            "cmd.exe",
    }
    exe = exe_map.get(app_name.lower(), app_name + ".exe")
    result = subprocess.run(
        ["taskkill", "/F", "/IM", exe],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return f"Closed {app_name}"
    return f"{app_name} was not running"


@function_tool
async def take_screenshot(context: RunContext) -> str:
    """Take a screenshot and save it to the Desktop."""
    import pyautogui, os
    path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
    pyautogui.screenshot(path)
    return f"Screenshot saved to Desktop"


@function_tool
async def screenshot_and_describe(context: RunContext, question: str = "What is on the screen?") -> str:
    """Take a screenshot and describe what is on screen using AI vision."""
    import pyautogui, anthropic, base64, io
    img = pyautogui.screenshot()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
            {"type": "text", "text": f"{question} Answer in 1-2 short sentences for voice output."}
        ]}]
    )
    return resp.content[0].text.strip()


@function_tool
async def keyboard_type(context: RunContext, text: str) -> str:
    """Type text at the current cursor position."""
    import pyautogui, pyperclip
    try:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        return f"Typed: {text}"
    except Exception as e:
        return f"Could not type: {e}"


@function_tool
async def keyboard_shortcut(context: RunContext, keys: str) -> str:
    """Press a keyboard shortcut like ctrl+c, alt+tab, win+d."""
    import pyautogui
    parts = [k.strip().lower() for k in keys.split("+")]
    pyautogui.hotkey(*parts)
    return f"Pressed {keys}"


@function_tool
async def set_volume(context: RunContext, level: int) -> str:
    """Set system volume from 0 to 100."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level / 100)), None)
        return f"Volume set to {level}%"
    except Exception as e:
        return f"Could not set volume: {e}"


@function_tool
async def read_file(context: RunContext, path: str) -> str:
    """Read text content from a file path."""
    import os
    try:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
            content = f.read()
        return content[:800] + ("..." if len(content) > 800 else "")
    except Exception as e:
        return f"Could not read file: {e}"


@function_tool
async def write_file(context: RunContext, path: str, content: str, mode: str = "write") -> str:
    """Write or append text to a file. mode='write' overwrites, mode='append' adds to end."""
    import os
    try:
        file_mode = "a" if mode == "append" else "w"
        full_path = os.path.expanduser(path)
        parent_dir = os.path.dirname(full_path) or "."
        os.makedirs(parent_dir, exist_ok=True)
        with open(full_path, file_mode, encoding="utf-8") as f:
            f.write(content)
        action = "Appended to" if mode == "append" else "Wrote to"
        return f"{action} {path}"
    except Exception as e:
        return f"Could not write file: {e}"


@function_tool
async def mouse_click(context: RunContext, x: int, y: int, button: str = "left", double: bool = False) -> str:
    """Click the mouse at screen coordinates (x, y). button='left'/'right'/'middle', double=True for double-click."""
    import pyautogui
    try:
        if double:
            pyautogui.doubleClick(x, y, button=button)
            return f"Double-clicked at ({x}, {y})"
        else:
            pyautogui.click(x, y, button=button)
            return f"Clicked at ({x}, {y})"
    except Exception as e:
        return f"Could not click: {e}"


@function_tool
async def list_running_apps(context: RunContext) -> str:
    """List currently running applications (process names and window titles)."""
    import subprocess
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()
        # Parse CSV: "Name","PID","Session Name","Session#","Mem Usage"
        seen, apps = set(), []
        MAX_APPS_TO_REPORT = 20
        for line in lines:
            parts = [p.strip('"') for p in line.split('","')]
            if parts:
                name = parts[0].lower().replace(".exe", "")
                if name not in seen and name not in {"system", "registry", "smss", "csrss",
                                                      "wininit", "services", "lsass", "svchost",
                                                      "dwm", "conhost", "tasklist"}:
                    seen.add(name)
                    apps.append(parts[0].replace(".exe", ""))
        if apps:
            return "Running: " + ", ".join(apps[:MAX_APPS_TO_REPORT])
        return "No user applications found"
    except Exception as e:
        return f"Could not list apps: {e}"


@function_tool
async def run_shell_command(context: RunContext, command: str) -> str:
    """Run a safe, read-only Windows shell command and return output. Good for: dir, echo, ipconfig, systeminfo, whoami, date, time, ver."""
    import subprocess
    # Safelist of allowed command prefixes — prevents destructive operations
    SAFE_PREFIXES = (
        "dir", "echo", "ipconfig", "whoami", "hostname", "ver", "date /t",
        "time /t", "systeminfo", "type", "where", "set", "path", "wmic",
        "netstat", "ping", "tracert", "nslookup", "vol", "cd", "tree",
    )
    MAX_COMMAND_OUTPUT_CHARS = 600
    cmd_lower = command.strip().lower()
    if not any(cmd_lower.startswith(p) for p in SAFE_PREFIXES):
        return f"Command not allowed for safety: '{command}'. Allowed: {', '.join(SAFE_PREFIXES)}"
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=8
        )
        output = (result.stdout or result.stderr or "").strip()
        return output[:MAX_COMMAND_OUTPUT_CHARS] + ("..." if len(output) > MAX_COMMAND_OUTPUT_CHARS else "") if output else "No output"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Command failed: {e}"


# ── Agent ──────────────────────────────────────────────────────────────────────

class LongLong(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=INSTRUCTIONS,
            tools=[
                get_weather,
                get_current_time,
                open_website,
                search_web,
                open_application,
                close_application,
                take_screenshot,
                screenshot_and_describe,
                keyboard_type,
                keyboard_shortcut,
                set_volume,
                read_file,
                write_file,
                mouse_click,
                list_running_apps,
                run_shell_command,
            ],
        )

    async def on_enter(self) -> None:
        """Greet the user when session starts."""
        await self.session.generate_reply(
            instructions="Greet the user as LongLong. Say something like: Hey, LongLong here! What can I do for you? Keep it short and friendly."
        )


# ── Entry point ────────────────────────────────────────────────────────────────

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    logger.info("龙龙 connected to room")

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-2",
            punctuate=True,
            smart_format=True,
            # No language= restriction → Deepgram auto-detects Chinese & English
        ),
        llm=lk_anthropic.LLM(
            model="claude-sonnet-4-5-20251001",  # upgraded from haiku for smarter reasoning
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        ),
        # TTS — Deepgram aura-2, confirmed working on free tier
        tts=deepgram.TTS(
            model="aura-2-asteria-en",
            api_key=os.getenv("DEEPGRAM_API_KEY", ""),
        ),
        # Interrupt handling — user can cut 龙龙 off mid-sentence
        allow_interruptions=True,
        min_interruption_duration=0.3,
        min_endpointing_delay=0.3,      # reduced: snappier turn detection
    )

    await session.start(
        room=ctx.room,
        agent=LongLong(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),  # background noise removal
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="longlong"))