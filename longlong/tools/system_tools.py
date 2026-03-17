"""
System Tools — Windows system control
"""

import os
import subprocess
import datetime


def get_current_time() -> str:
    now = datetime.datetime.now()
    return now.strftime("Current time is %I:%M %p, %A %B %d, %Y")


def open_application(app_name: str) -> str:
    """Open a Windows application by name."""
    app_map = {
        "notepad":      "notepad.exe",
        "calculator":   "calc.exe",
        "paint":        "mspaint.exe",
        "file explorer":"explorer.exe",
        "explorer":     "explorer.exe",
        "task manager": "taskmgr.exe",
        "spotify":      "spotify.exe",
        "word":         "WINWORD.EXE",
        "excel":        "EXCEL.EXE",
        "powerpoint":   "POWERPNT.EXE",
        "vscode":       "code",
        "vs code":      "code",
    }
    exe = app_map.get(app_name.lower(), app_name)
    try:
        subprocess.Popen(exe, shell=True)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Could not open {app_name}: {e}"


def take_screenshot() -> str:
    """Take a screenshot and save to Desktop."""
    try:
        import pyautogui
        path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(path)
        return f"Screenshot saved to {path}"
    except Exception as e:
        return f"Screenshot failed: {e}"


def set_volume(level: int) -> str:
    """Set system volume 0-100 on Windows."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        import math
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        # Convert 0-100 to dB
        if level == 0:
            volume.SetMasterVolumeLevel(-65.25, None)
        else:
            db = 20 * math.log10(level / 100)
            volume.SetMasterVolumeLevel(db, None)
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
        "description": "Open a Windows application like Notepad, Calculator, Spotify, VS Code, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "App name e.g. 'notepad', 'spotify', 'vscode'"},
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "take_screenshot",
        "description": "Take a screenshot of the current screen.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "set_volume",
        "description": "Set the system speaker volume.",
        "input_schema": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "description": "Volume level 0-100"},
            },
            "required": ["level"],
        },
    },
]

HANDLERS = {
    "get_current_time":  get_current_time,
    "open_application":  open_application,
    "take_screenshot":   take_screenshot,
    "set_volume":        set_volume,
}
