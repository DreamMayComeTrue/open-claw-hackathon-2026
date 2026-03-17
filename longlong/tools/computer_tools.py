"""
Computer Control Tools — mouse, keyboard, screen vision
"龙龙 click the submit button"
"龙龙 type hello world"
"龙龙 what's on my screen?"
"""

import os
import time
import base64
import pyautogui
import pyperclip
from utils.display import print_status

# Safety — stops pyautogui if mouse hits corner
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3  # small delay between actions for stability


# ── Mouse ──────────────────────────────────────────

def mouse_click(x: int = None, y: int = None, button: str = "left") -> str:
    """Click mouse at position or current position."""
    try:
        if x and y:
            pyautogui.click(x, y, button=button)
            return f"Clicked {button} at ({x}, {y})"
        else:
            pyautogui.click(button=button)
            pos = pyautogui.position()
            return f"Clicked {button} at current position ({pos.x}, {pos.y})"
    except Exception as e:
        return f"Click failed: {e}"


def mouse_move(x: int, y: int) -> str:
    """Move mouse to position."""
    try:
        pyautogui.moveTo(x, y, duration=0.3)
        return f"Mouse moved to ({x}, {y})"
    except Exception as e:
        return f"Move failed: {e}"


def mouse_scroll(direction: str = "down", amount: int = 3) -> str:
    """Scroll up or down."""
    try:
        clicks = -amount if direction == "down" else amount
        pyautogui.scroll(clicks)
        return f"Scrolled {direction} {amount} times"
    except Exception as e:
        return f"Scroll failed: {e}"


# ── Keyboard ───────────────────────────────────────

def keyboard_type(text: str) -> str:
    """Type text at current cursor position."""
    try:
        pyautogui.typewrite(text, interval=0.04)
        return f"Typed: {text}"
    except Exception as e:
        # Fallback for unicode/Chinese — use clipboard paste
        try:
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            return f"Typed (via clipboard): {text}"
        except Exception as e2:
            return f"Type failed: {e2}"


def keyboard_shortcut(keys: str) -> str:
    """
    Press a keyboard shortcut.
    Examples: 'ctrl+c', 'alt+tab', 'win+d', 'ctrl+shift+t'
    """
    try:
        parts = [k.strip().lower() for k in keys.split("+")]
        pyautogui.hotkey(*parts)
        return f"Pressed: {keys}"
    except Exception as e:
        return f"Shortcut failed: {e}"


def keyboard_press(key: str) -> str:
    """Press a single key like enter, escape, tab, delete, backspace."""
    try:
        pyautogui.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Key press failed: {e}"


# ── Screen Vision ──────────────────────────────────

def screenshot_and_describe(question: str = "What is on the screen?") -> str:
    """
    Take a screenshot and ask Claude to describe/analyze it.
    This is the 'see my screen' Jarvis feature.
    """
    try:
        import anthropic
        from dotenv import load_dotenv
        load_dotenv()

        # Take screenshot
        img = pyautogui.screenshot()

        # Convert to base64
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        # Ask Claude vision
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"{question} Answer in 2-3 short sentences suitable for voice. Be specific about what you see."
                    }
                ],
            }]
        )
        return response.content[0].text.strip()

    except Exception as e:
        return f"Screen vision failed: {e}"


def get_mouse_position() -> str:
    """Get current mouse position — useful for debugging."""
    pos = pyautogui.position()
    size = pyautogui.size()
    return f"Mouse at ({pos.x}, {pos.y}). Screen size: {size.width}x{size.height}"


def find_and_click(image_description: str) -> str:
    """
    Take screenshot, ask Claude where something is, then click it.
    e.g. 'find and click the submit button'
    """
    try:
        import anthropic
        from dotenv import load_dotenv
        load_dotenv()

        img = pyautogui.screenshot()
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
                    },
                    {
                        "type": "text",
                        "text": f"Find '{image_description}' on screen. Reply ONLY with: x,y coordinates as two numbers separated by comma. Example: 450,320. Nothing else."
                    }
                ],
            }]
        )

        coords = response.content[0].text.strip()
        x, y = map(int, coords.split(","))
        pyautogui.click(x, y)
        return f"Found and clicked '{image_description}' at ({x}, {y})"

    except Exception as e:
        return f"Find and click failed: {e}"


# ── Tool definitions for Claude ────────────────────

DEFINITIONS = [
    {
        "name": "mouse_click",
        "description": "Click the mouse at a specific position or current position.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x":      {"type": "integer", "description": "X coordinate (optional)"},
                "y":      {"type": "integer", "description": "Y coordinate (optional)"},
                "button": {"type": "string",  "description": "left, right, or middle. Default left"},
            },
        },
    },
    {
        "name": "mouse_move",
        "description": "Move mouse cursor to a specific position on screen.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate"},
                "y": {"type": "integer", "description": "Y coordinate"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "mouse_scroll",
        "description": "Scroll the mouse wheel up or down.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string",  "description": "up or down"},
                "amount":    {"type": "integer", "description": "Number of scroll clicks, default 3"},
            },
        },
    },
    {
        "name": "keyboard_type",
        "description": "Type text at the current cursor position. Supports Chinese and English.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "keyboard_shortcut",
        "description": "Press a keyboard shortcut like ctrl+c, alt+tab, win+d, ctrl+shift+t.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keys": {"type": "string", "description": "Keys joined by +, e.g. ctrl+c or alt+tab"},
            },
            "required": ["keys"],
        },
    },
    {
        "name": "keyboard_press",
        "description": "Press a single key like enter, escape, tab, delete, backspace, space.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key name: enter, escape, tab, delete, backspace, space, up, down, left, right"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "screenshot_and_describe",
        "description": "Take a screenshot and describe what is on screen. Use when user asks what is on screen, what is open, what do you see, describe my screen, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "What to look for or ask about the screen"},
            },
        },
    },
    {
        "name": "find_and_click",
        "description": "Find a UI element on screen by description and click it. e.g. 'submit button', 'close button', 'search box'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_description": {"type": "string", "description": "Description of the element to find and click"},
            },
            "required": ["image_description"],
        },
    },
    {
        "name": "get_mouse_position",
        "description": "Get the current mouse cursor position and screen size.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "mouse_click":             mouse_click,
    "mouse_move":              mouse_move,
    "mouse_scroll":            mouse_scroll,
    "keyboard_type":           keyboard_type,
    "keyboard_shortcut":       keyboard_shortcut,
    "keyboard_press":          keyboard_press,
    "screenshot_and_describe": screenshot_and_describe,
    "find_and_click":          find_and_click,
    "get_mouse_position":      get_mouse_position,
}