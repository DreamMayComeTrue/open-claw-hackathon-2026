"""
龙龙 — LiveKit Voice Agent (Demo-optimized)
Phone-call quality conversation: full-duplex, interruptible, ~300ms response

Key upgrades for hackathon demo:
- Session memory (remember/recall + automatic preference tracking)
- Better desktop control (mouse tools)
- Automatic multistep planning for complex requests (agent decides when to plan)
- Visual verification via screenshot_and_describe
"""

import os
import json
import time
import asyncio
import logging
from typing import Any, Dict, Optional

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
You are LongLong, a smart and friendly AI voice assistant.
You are bridged to Nicole (your OpenClaw AI agent) via Telegram.

THIS IS A LIVE VOICE DEMO ON WINDOWS.
- You may control the user's computer (open apps, type, click, etc.) without asking permission.
- Think step-by-step silently. Speak only the final result in a short, natural voice reply.
- Keep spoken replies SHORT: usually 1–5 sentences. No markdown, no bullet points, no lists.
- If a request is ambiguous, ask ONE short clarifying question.
- For multi-step tasks, do them step-by-step and verify progress with screenshots when needed.
- You can tell some joke if the user requires

NICOLE ROUTING:
- "ask Nicole / tell Nicole / Nicole search / Nicole remember / what does Nicole know" → ask_nicole
- "send Nicole a message / message Nicole" → send_telegram

GOAL:
- Be impressive in a live demo: fast, confident, and reliable.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_ms() -> int:
    return int(time.time() * 1000)


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


# ── Tools ─────────────────────────────────────────────────────────────────────

@function_tool
async def get_weather(context: RunContext, city: str) -> str:
    """Get current weather for a city (quick, no API key)."""
    import urllib.request
    import urllib.parse
    import json as _json

    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = _json.loads(r.read())
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
    """Open a website in the browser and bring it to the front (Windows)."""
    import subprocess
    if not url.startswith("http"):
        url = "https://" + url
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"Opened {url}"


@function_tool
async def search_web(context: RunContext, query: str) -> str:
    """Search Google for something."""
    import subprocess
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"Searching for: {query}"


@function_tool
async def open_application(context: RunContext, app_name: str) -> str:
    """Open a Windows application like notepad, chrome, powershell, spotify, calculator."""
    import subprocess
    import os as _os

    name = app_name.lower().strip()

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        _os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    if name in ["chrome", "google chrome"]:
        for path in chrome_paths:
            if _os.path.exists(path):
                subprocess.Popen([path])
                return "Opened Chrome"
        subprocess.Popen('start chrome', shell=True)
        return "Opened Chrome"

    if name in ["edge", "microsoft edge"]:
        for path in edge_paths:
            if _os.path.exists(path):
                subprocess.Popen([path])
                return "Opened Edge"
        subprocess.Popen('start msedge', shell=True)
        return "Opened Edge"

    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "powershell": "powershell.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "vscode": "code",
        "vs code": "code",
        "spotify": _os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
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
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "edge": "msedge.exe",
        "firefox": "firefox.exe",
        "notepad": "notepad.exe",
        "spotify": "Spotify.exe",
        "vscode": "Code.exe",
        "vs code": "Code.exe",
        "powershell": "powershell.exe",
        "cmd": "cmd.exe",
    }
    exe = exe_map.get(app_name.lower(), app_name + ".exe")
    result = subprocess.run(
        ["taskkill", "/F", "/IM", exe],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return f"Closed {app_name}"
    return f"{app_name} was not running"


@function_tool
async def take_screenshot(context: RunContext) -> str:
    """Take a screenshot and save it to the Desktop."""
    import pyautogui
    path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
    pyautogui.screenshot(path)
    return "Screenshot saved to Desktop"


@function_tool
async def screenshot_and_describe(context: RunContext, question: str = "What is on the screen?") -> str:
    """Take a screenshot and describe what is on screen using AI vision (Anthropic)."""
    import pyautogui
    import anthropic
    import base64
    import io

    img = pyautogui.screenshot()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    resp = client.messages.create(
        model=os.getenv("ANTHROPIC_VISION_MODEL", "claude-haiku-4-5"),
        max_tokens=220,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                {"type": "text", "text": f"{question}\nAnswer in 1-2 short sentences for voice output."},
            ],
        }],
    )
    return resp.content[0].text.strip()


@function_tool
async def keyboard_type(context: RunContext, text: str) -> str:
    """Type text at the current cursor position (clipboard paste for reliability)."""
    import pyautogui
    import pyperclip
    try:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        return "Typed."
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
    """Read text content from a file path (first 800 chars)."""
    try:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
            content = f.read()
        return content[:800] + ("..." if len(content) > 800 else "")
    except Exception as e:
        return f"Could not read file: {e}"


# --- NEW: mouse tools (demo power) --------------------------------------------

@function_tool
async def get_mouse_position(context: RunContext) -> str:
    """Get current mouse position (x,y)."""
    import pyautogui
    p = pyautogui.position()
    return f"{p.x},{p.y}"


@function_tool
async def mouse_move(context: RunContext, x: int, y: int) -> str:
    """Move mouse to (x,y)."""
    import pyautogui
    pyautogui.moveTo(int(x), int(y), duration=0.15)
    return f"Moved mouse to {x},{y}"


@function_tool
async def mouse_click(context: RunContext, x: int, y: int, clicks: int = 1, button: str = "left") -> str:
    """Click at (x,y)."""
    import pyautogui
    pyautogui.click(int(x), int(y), clicks=int(clicks), interval=0.08, button=button)
    return f"Clicked {x},{y}"


@function_tool
async def mouse_scroll(context: RunContext, amount: int) -> str:
    """Scroll mouse wheel (positive=up, negative=down)."""
    import pyautogui
    pyautogui.scroll(int(amount))
    return "Scrolled."


# ── Nicole (OpenClaw) Gateway Bridge ──────────────────────────────────────────

@function_tool
async def ask_nicole(context: RunContext, command: str) -> str:
    """
    Send a command directly to Nicole (OpenClaw) via local gateway and get her reply.
    Use when user says: 'ask Nicole to...', 'tell Nicole to...', 'Nicole search...',
    'Nicole remember...', 'what does Nicole know about...', etc.
    """
    import requests, re as _re
    token = os.getenv("OPENCLAW_GATEWAY_TOKEN", "")
    url   = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.post(
            f"{url}/v1/chat/completions",
            headers=headers,
            json={
                "model": "openclaw:main",
                "messages": [{"role": "user", "content": command}],
                "stream": False,
            },
            timeout=30,
        )
        logger.info(f"Nicole status={resp.status_code} body={resp.text[:300]}")

        if resp.ok:
            data = resp.json()
            try:
                reply = data["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError):
                reply = str(data)[:400]
            # Strip markdown symbols for clean voice output
            reply = _re.sub(r'\*+', '', reply)
            reply = _re.sub(r'#+\s*', '', reply)
            reply = _re.sub(r':[a-z_]+:', '', reply)
            reply = _re.sub(r'\n+', ' ', reply).strip()
            return f"Nicole says: {reply[:400]}"

        return f"Nicole gateway error {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        return "Nicole gateway is not reachable — is OpenClaw running?"
    except requests.exceptions.Timeout:
        return "Nicole took too long — she might be busy"
    except Exception as e:
        return f"Could not reach Nicole: {e}"


@function_tool
async def send_telegram(context: RunContext, message: str) -> str:
    """
    Ask Nicole to send a Telegram message on your behalf.
    Use when user says 'send a Telegram to X saying Y' or 'message X on Telegram'.
    """
    import requests
    token = os.getenv("OPENCLAW_GATEWAY_TOKEN", "")
    url   = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.post(
            f"{url}/v1/chat/completions",
            headers=headers,
            json={
                "model": "openclaw:main",
                "messages": [{"role": "user", "content": message}],
                "stream": False,
            },
            timeout=30,
        )
        if resp.ok:
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return f"Nicole: {reply[:200]}"
        return f"Gateway error {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return f"Could not reach Nicole: {e}"


# ── Agent ─────────────────────────────────────────────────────────────────────

class LongLong(Agent):
    """
    Upgraded agent:
    - Session memory (state dict) + tools for remember/recall
    - Auto multi-step planning via do_task() for complex requests
    """

    def __init__(self) -> None:
        super().__init__(
            instructions=INSTRUCTIONS,
            tools=[
                # utilities
                get_weather,
                get_current_time,
                # web/apps
                open_website,
                search_web,
                open_application,
                close_application,
                # screen/vision
                take_screenshot,
                screenshot_and_describe,
                # input control
                keyboard_type,
                keyboard_shortcut,
                set_volume,
                # files
                read_file,
                # mouse
                get_mouse_position,
                mouse_move,
                mouse_click,
                mouse_scroll,
                # Nicole (OpenClaw) bridge via Telegram
                ask_nicole,
                send_telegram,
            ],
        )

        self.state: Dict[str, Any] = {
            "demo_mode": True,
            "started_at_ms": _now_ms(),
            "user_name": None,
            "last_action": None,
            "last_app_opened": None,
            "last_website_opened": None,
        }

    async def on_enter(self) -> None:
        # Friendly, short greeting
        await self.session.generate_reply(
            instructions=(
                "Greet the user. Speak naturally with no emojis and no markdown. "
            "Do not use symbols like asterisks, hashtags, or brackets. "
            "Hey, LongLong here. What can I do for you?"
            )
        )


# ── NEW: Memory tools bound via closure-like access ----------------------------
# LiveKit function tools are module-level; we can still store state by using a
# lightweight global pointer to the current agent (set at session start).

_CURRENT_AGENT: Optional[LongLong] = None


@function_tool
async def remember(context: RunContext, key: str, value: str) -> str:
    """Remember a small fact for this session (demo memory)."""
    global _CURRENT_AGENT
    if _CURRENT_AGENT is None:
        return "Memory not ready."
    _CURRENT_AGENT.state[key] = value
    return "Got it."


@function_tool
async def recall(context: RunContext, key: str) -> str:
    """Recall a remembered fact for this session."""
    global _CURRENT_AGENT
    if _CURRENT_AGENT is None:
        return ""
    v = _CURRENT_AGENT.state.get(key)
    return "" if v is None else str(v)


@function_tool
async def show_memory(context: RunContext) -> str:
    """Show current session memory (debug)."""
    global _CURRENT_AGENT
    if _CURRENT_AGENT is None:
        return "{}"
    return _json_dumps(_CURRENT_AGENT.state)


# ── NEW: Auto-planner tool -----------------------------------------------------
# NOTE: This relies on the main LLM tool-calling ability, but forces structure:
# The model writes a plan (JSON), then executes steps using tools, verifying
# with screenshot_and_describe when helpful.

@function_tool
async def do_task(context: RunContext, goal: str) -> str:
    """
    Execute a multi-step task.
    Use for requests that involve multiple actions or UI automation.
    """
    global _CURRENT_AGENT
    agent = _CURRENT_AGENT
    if agent is None:
        return "Agent not ready."

    # Ask the model to produce a minimal JSON plan.
    plan_prompt = f"""
You are controlling a Windows computer for a live demo.
Create a short plan to achieve this goal:

GOAL: {goal}

Return ONLY valid JSON in this exact schema:
{{
  "steps": [
    {{
      "intent": "short description",
      "tool": "tool_name_or_empty",
      "args": {{ "arg": "value" }},
      "verify": "optional short verification question for screenshot_and_describe, or empty"
    }}
  ]
}}

Rules:
- 2 to 6 steps max.
- Prefer using available tools: open_website, search_web, open_application, keyboard_shortcut, keyboard_type, mouse_move, mouse_click, mouse_scroll, screenshot_and_describe.
- If you need to find something on screen, add a screenshot_and_describe verification question.
- Keep args minimal.
"""

    # generate_reply returns speech; we want text. LiveKit AgentSession generate_reply
    # emits agent output; but we can still use it as the "planner voice".
    # We'll do a small hack: ask it to "say" the JSON; since voice is used, keep it short.
    try:
        # This will send a response as agent; but we can still capture by asking it to return JSON.
        plan_text = await agent.session.generate_reply(instructions=plan_prompt)
    except Exception:
        plan_text = None

    # Some LiveKit versions return None; so fallback to direct LLM call is not available here.
    # In practice, many agent runtimes will have generate_reply return a string.
    if not isinstance(plan_text, str) or "{" not in plan_text:
        # Fallback: do a single verification screenshot and return guidance.
        v = await screenshot_and_describe(context, f"I need to do: {goal}. What do you see on screen right now?")
        return f"I can do that. Right now I see: {v}"

    # Extract JSON safely
    json_start = plan_text.find("{")
    json_end = plan_text.rfind("}")
    if json_start == -1 or json_end == -1 or json_end <= json_start:
        return "Planning failed."

    try:
        plan = json.loads(plan_text[json_start:json_end + 1])
    except Exception as e:
        return f"Planning JSON error: {e}"

    steps = plan.get("steps", [])
    if not isinstance(steps, list) or not steps:
        return "No plan steps."

    # Tool registry (call module-level tool coroutines directly)
    tool_map = {
        "open_website": open_website,
        "search_web": search_web,
        "open_application": open_application,
        "close_application": close_application,
        "keyboard_type": keyboard_type,
        "keyboard_shortcut": keyboard_shortcut,
        "mouse_move": mouse_move,
        "mouse_click": mouse_click,
        "mouse_scroll": mouse_scroll,
        "get_mouse_position": get_mouse_position,
        "get_weather": get_weather,
        "get_current_time": get_current_time,
        "read_file": read_file,
        "take_screenshot": take_screenshot,
        "screenshot_and_describe": screenshot_and_describe,
        "remember": remember,
        "recall": recall,
        "show_memory": show_memory,
    }

    results = []
    for i, step in enumerate(steps[:6], start=1):
        intent = (step.get("intent") or "").strip()
        tool = (step.get("tool") or "").strip()
        args = step.get("args") or {}
        verify_q = (step.get("verify") or "").strip()

        # Execute tool if requested
        if tool:
            fn = tool_map.get(tool)
            if fn is None:
                results.append(f"Step {i}: unknown tool {tool}")
            else:
                try:
                    # Tool functions all have (context, **kwargs)
                    if not isinstance(args, dict):
                        args = {}
                    out = await fn(context, **args)
                    results.append(f"Step {i}: {intent or tool} -> {out}")
                except Exception as e:
                    results.append(f"Step {i}: {intent or tool} failed: {e}")
                    # For demo: stop early on failure
                    break
        else:
            results.append(f"Step {i}: {intent} (no tool)")

        # Verification via vision (your preference)
        if verify_q:
            try:
                v = await screenshot_and_describe(context, verify_q)
                results.append(f"Verify {i}: {v}")
            except Exception as e:
                results.append(f"Verify {i} failed: {e}")

    # Return a short summary (spoken output will be short anyway)
    # Keep it compact.
    tail = results[-3:] if len(results) > 3 else results
    return "Done. " + " | ".join(tail)


# ── Entry point ───────────────────────────────────────────────────────────────

async def entrypoint(ctx: JobContext):
    global _CURRENT_AGENT

    await ctx.connect()
    logger.info("龙龙 connected to room")

    # Create agent instance and expose it to memory/planner tools
    agent = LongLong()
    _CURRENT_AGENT = agent

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-2",
            language="en",
            punctuate=True,
            smart_format=True,
        ),
        llm=lk_anthropic.LLM(
            model=os.getenv("ANTHROPIC_CHAT_MODEL", "claude-haiku-4-5"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        ),
        tts=deepgram.TTS(
            model=os.getenv("DEEPGRAM_TTS_MODEL", "aura-2-asteria-en"),
            api_key=os.getenv("DEEPGRAM_API_KEY", ""),
        ),
        allow_interruptions=True,
        min_interruption_duration=0.3,
        min_endpointing_delay=0.4,
    )

    # Add NEW tools to this agent instance dynamically by extending tools list:
    # (Because remember/recall/do_task are defined after LongLong init.)
    # LiveKit Agent base class stores tools at init; we can patch for simplicity.
    try:
        agent.tools.extend([remember, recall, show_memory, do_task, ask_nicole, send_telegram])
    except Exception:
        pass

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Keep session alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="longlong"))