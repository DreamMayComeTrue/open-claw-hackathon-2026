"""
System Tools — Windows, actually tested
"""

import os
import subprocess
import datetime


def get_current_time() -> str:
    now = datetime.datetime.now()
    return now.strftime("Current time is %I:%M %p, %A %B %d, %Y")


def open_application(app_name: str) -> str:
    """Open Windows applications — uses multiple methods to ensure it works."""
    name = app_name.lower().strip()

    # Direct executable map
    app_map = {
        "notepad":        "notepad.exe",
        "calculator":     "calc.exe",
        "paint":          "mspaint.exe",
        "explorer":       "explorer.exe",
        "file explorer":  "explorer.exe",
        "task manager":   "taskmgr.exe",
        "cmd":            "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell":     "powershell.exe",
        "word":           "WINWORD.EXE",
        "excel":          "EXCEL.EXE",
        "powerpoint":     "POWERPNT.EXE",
        "vscode":         "code.exe",
        "vs code":        "code.exe",
        "chrome":         "chrome.exe",
        "edge":           "msedge.exe",
        "firefox":        "firefox.exe",
    }

    exe = app_map.get(name)

    # Spotify special case — find in AppData
    if name == "spotify":
        spotify_path = os.path.join(
            os.environ.get("APPDATA", ""),
            "Spotify", "Spotify.exe"
        )
        if os.path.exists(spotify_path):
            subprocess.Popen([spotify_path])
            return "Opened Spotify"
        else:
            subprocess.Popen(["start", "spotify:"], shell=True)
            return "Opening Spotify via URI"

    if exe:
        try:
            subprocess.Popen(exe, shell=True)
            return f"Opened {app_name}"
        except Exception as e:
            return f"Failed to open {app_name}: {e}"

    # Try running directly as typed
    try:
        subprocess.Popen(app_name, shell=True)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Could not open '{app_name}': {e}"


def close_application(app_name: str) -> str:
    """Force close any Windows application by name."""
    name = app_name.lower().strip()
    exe_map = {
        "chrome":         "chrome.exe",
        "edge":           "msedge.exe",
        "firefox":        "firefox.exe",
        "notepad":        "notepad.exe",
        "spotify":        "spotify.exe",
        "vscode":         "code.exe",
        "vs code":        "code.exe",
        "word":           "WINWORD.EXE",
        "excel":          "EXCEL.EXE",
        "powershell":     "powershell.exe",
        "cmd":            "cmd.exe",
    }
    exe = exe_map.get(name, app_name if app_name.endswith(".exe") else app_name + ".exe")
    result = subprocess.run(
        ["taskkill", "/F", "/IM", exe],
        capture_output=True, text=True
    )
    if "SUCCESS" in result.stdout or result.returncode == 0:
        return f"Closed {app_name}"
    return f"Could not close {app_name} — it may not be running"


def take_screenshot() -> str:
    try:
        import pyautogui
        path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(path)
        return f"Screenshot saved to Desktop"
    except Exception as e:
        return f"Screenshot failed: {e}"


def set_volume(level: int) -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        import math
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        scalar = max(0.0, min(1.0, level / 100))
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return f"Volume set to {level}%"
    except Exception as e:
        return f"Could not set volume: {e}"


DEFINITIONS = [
    {
        "name": "get_current_time",
        "description": "Get the current date and time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "open_application",
        "description": "Open a Windows application. Supports: notepad, calculator, powershell, cmd, chrome, edge, spotify, vscode, word, excel, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "App name to open"},
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "close_application",
        "description": "Force close any Windows application by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "App name to close, e.g. chrome, spotify, notepad"},
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "take_screenshot",
        "description": "Take a screenshot and save it to the Desktop.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "set_volume",
        "description": "Set system speaker volume 0-100.",
        "input_schema": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "description": "Volume 0-100"},
            },
            "required": ["level"],
        },
    },
]

HANDLERS = {
    "get_current_time":  get_current_time,
    "open_application":  open_application,
    "close_application": close_application,
    "take_screenshot":   take_screenshot,
    "set_volume":        set_volume,
}