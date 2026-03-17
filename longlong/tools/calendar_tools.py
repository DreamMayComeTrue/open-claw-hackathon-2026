"""
Google Calendar Tools for 小宝
"""

import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def _get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def create_event(title: str, start_time: str, duration_minutes: int = 60, description: str = "") -> str:
    """Create a calendar event. start_time format: 'YYYY-MM-DDTHH:MM:SS'"""
    try:
        service = _get_service()
        start = datetime.datetime.fromisoformat(start_time)
        end = start + datetime.timedelta(minutes=duration_minutes)
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kuala_Lumpur"},
            "end":   {"dateTime": end.isoformat(),   "timeZone": "Asia/Kuala_Lumpur"},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"Event created: {created.get('summary')} at {start_time}"
    except Exception as e:
        return f"Failed to create event: {e}"


def list_events(max_results: int = 5) -> str:
    """List upcoming calendar events."""
    try:
        service = _get_service()
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])
        if not events:
            return "No upcoming events."
        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            lines.append(f"- {e['summary']} at {start}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list events: {e}"


def delete_event(title: str) -> str:
    """Delete the next upcoming event matching the title."""
    try:
        service = _get_service()
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        for e in events_result.get("items", []):
            if title.lower() in e.get("summary", "").lower():
                service.events().delete(calendarId="primary", eventId=e["id"]).execute()
                return f"Deleted event: {e['summary']}"
        return f"No event found matching '{title}'"
    except Exception as e:
        return f"Failed to delete event: {e}"


# Claude tool definitions
DEFINITIONS = [
    {
        "name": "create_event",
        "description": "Create a new event on the user's Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":            {"type": "string",  "description": "Event title"},
                "start_time":       {"type": "string",  "description": "ISO format: YYYY-MM-DDTHH:MM:SS"},
                "duration_minutes": {"type": "integer", "description": "Duration in minutes, default 60"},
                "description":      {"type": "string",  "description": "Optional event description"},
            },
            "required": ["title", "start_time"],
        },
    },
    {
        "name": "list_events",
        "description": "List upcoming events on the user's Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Max number of events to return, default 5"},
            },
        },
    },
    {
        "name": "delete_event",
        "description": "Delete an upcoming calendar event by title.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title or partial title of the event to delete"},
            },
            "required": ["title"],
        },
    },
]

HANDLERS = {
    "create_event": create_event,
    "list_events":  list_events,
    "delete_event": delete_event,
}
