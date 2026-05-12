from __future__ import print_function
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE        = "token.json"

# Pastel-ish subset of Google Calendar's 11 built-in event colors.
# colorId reference:
#   1  Lavender   6  Tangerine
#   2  Sage       7  Peacock
#   4  Flamingo
#   5  Banana
PASTEL_COLOR_IDS = [1, 2, 4, 5, 6, 7]


def get_calendar_service():
    """
    Handles OAuth2 auth, refreshing or re-running the flow as needed.
    Reuses token.json if valid.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def insert_weekly_event(service, summary: str, location: str,
                        start_dt, end_dt, rrule: str, timezone: str,
                        color_id: int | None = None) -> dict:
    """
    Inserts a single weekly recurring event into the primary calendar.

    :param color_id: Google Calendar colorId (1–11). If None, uses calendar default.
    """
    event_body = {
        "summary":    summary,
        "location":   location,
        "start":      {"dateTime": start_dt.isoformat(), "timeZone": timezone},
        "end":        {"dateTime": end_dt.isoformat(),   "timeZone": timezone},
        "recurrence": [rrule],
    }

    if color_id is not None:
        event_body["colorId"] = str(color_id)

    try:
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return event
    except HttpError as e:
        print(f"  [ERROR] Calendar API error for '{summary}': {e}")
        return {}
