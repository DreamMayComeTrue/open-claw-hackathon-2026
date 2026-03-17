"""
File Tools — read text files, list folders
"""

import os


def read_file(path: str) -> str:
    """Read text content from a file path."""
    try:
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # Truncate very long files for voice
        if len(content) > 1000:
            return content[:1000] + f"\n... (file truncated, {len(content)} chars total)"
        return content
    except Exception as e:
        return f"Could not read file: {e}"


def list_folder(path: str = ".") -> str:
    """List files and folders at a given path."""
    try:
        path = os.path.expanduser(path)
        items = os.listdir(path)
        files = [f for f in items if os.path.isfile(os.path.join(path, f))]
        dirs  = [d for d in items if os.path.isdir(os.path.join(path, d))]
        result = []
        if dirs:
            result.append("Folders: " + ", ".join(dirs[:10]))
        if files:
            result.append("Files: " + ", ".join(files[:10]))
        return "\n".join(result) or "Empty folder."
    except Exception as e:
        return f"Could not list folder: {e}"


DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read the text content of a file from its path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path, e.g. C:/Users/me/notes.txt or ~/documents/report.txt"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_folder",
        "description": "List files and folders in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Folder path, default is current directory"},
            },
        },
    },
]

HANDLERS = {
    "read_file":   read_file,
    "list_folder": list_folder,
}
