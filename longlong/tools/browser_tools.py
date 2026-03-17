"""
Browser Tools — Windows-specific, actually works
"""

import webbrowser
import subprocess
import urllib.parse
import time


def open_website(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def search_web(query: str) -> str:
    encoded = urllib.parse.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={encoded}")
    return f"Searched for: {query}"


def open_youtube_search(query: str) -> str:
    encoded = urllib.parse.quote(query)
    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
    return f"Opened YouTube search for: {query}"


def close_browser() -> str:
    """Force close all browsers on Windows."""
    closed = []
    browsers = {
        "chrome.exe": "Chrome",
        "msedge.exe": "Edge",
        "firefox.exe": "Firefox",
        "brave.exe": "Brave",
    }
    for exe, name in browsers.items():
        result = subprocess.run(
            ["taskkill", "/F", "/IM", exe],
            capture_output=True, text=True
        )
        if "SUCCESS" in result.stdout or "成功" in result.stdout:
            closed.append(name)
    if closed:
        return f"Closed: {', '.join(closed)}"
    return "No browsers were open"


DEFINITIONS = [
    {
        "name": "open_website",
        "description": "Open a website URL in the browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to open"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "search_web",
        "description": "Search Google for something.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "open_youtube_search",
        "description": "Search YouTube for a video.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "YouTube search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "close_browser",
        "description": "Force close all open browsers (Chrome, Edge, Firefox, Brave).",
        "input_schema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "open_website":        open_website,
    "search_web":          search_web,
    "open_youtube_search": open_youtube_search,
    "close_browser":       close_browser,
}