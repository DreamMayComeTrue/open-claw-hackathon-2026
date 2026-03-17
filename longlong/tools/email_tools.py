"""
Email Tools — send/read email via Gmail API
"""

import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

def _get_gmail():
    creds = None
    token_file = "gmail_token.json"
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def send_email(to: str, subject: str, body: str) -> str:
    try:
        service = _get_gmail()
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return f"Email sent to {to} with subject '{subject}'"
    except Exception as e:
        return f"Failed to send email: {e}"


def read_latest_emails(max_results: int = 3) -> str:
    try:
        service = _get_gmail()
        results = service.users().messages().list(
            userId="me", labelIds=["INBOX"], maxResults=max_results
        ).execute()
        messages = results.get("messages", [])
        if not messages:
            return "No emails found."
        output = []
        for msg in messages:
            detail = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            output.append(f"From: {headers.get('From','?')} | {headers.get('Subject','?')}")
        return "\n".join(output)
    except Exception as e:
        return f"Failed to read emails: {e}"


EMAIL_DEFINITIONS = [
    {
        "name": "send_email",
        "description": "Send an email via Gmail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body":    {"type": "string", "description": "Email body text"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "read_latest_emails",
        "description": "Read the latest emails from Gmail inbox.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Number of emails, default 3"},
            },
        },
    },
]

EMAIL_HANDLERS = {
    "send_email":        send_email,
    "read_latest_emails": read_latest_emails,
}

# Re-export for tools/__init__ compatibility
DEFINITIONS = EMAIL_DEFINITIONS
HANDLERS    = EMAIL_HANDLERS
