"""
Browser Tools — open/close websites, web search
Uses webbrowser (built-in) + pygetwindow for window control on Windows
"""

import webbrowser
import subprocess
import urllib.parse


def open_website(url: str) -> str:
    """Open a URL in the default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def search_web(query: str) -> str:
    """Search Google for a query."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"Searched for: {query}"


def open_youtube_search(query: str) -> str:
    """Search YouTube for a query."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    webbrowser.open(url)
    return f"Opened YouTube search for: {query}"


def close_browser() -> str:
    """Close Chrome or Edge on Windows."""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], capture_output=True)
        return "Browser closed."
    except Exception as e:
        return f"Could not close browser: {e}"


DEFINITIONS = [
    {
        "name": "open_website",
        "description": "Open a website URL in the browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to open, e.g. youtube.com or https://github.com"},
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
        "description": "Close the browser window.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "open_website":        open_website,
    "search_web":          search_web,
    "open_youtube_search": open_youtube_search,
    "close_browser":       close_browser,
}
