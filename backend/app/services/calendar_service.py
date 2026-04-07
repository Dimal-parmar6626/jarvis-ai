"""Calendar service: Google Calendar API integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CalendarService:
    """Interact with Google Calendar API."""

    def __init__(self, credentials_file: Optional[str] = None):
        self.credentials_file = credentials_file
        self._service = None

    def _get_service(self):
        """Lazily initialise the Google Calendar service."""
        if self._service is not None:
            return self._service
        try:
            from google.oauth2 import service_account  # type: ignore
            from googleapiclient.discovery import build  # type: ignore

            SCOPES = ["https://www.googleapis.com/auth/calendar"]
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            self._service = build("calendar", "v3", credentials=creds)
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).warning("Google Calendar unavailable: %s", exc)
            self._service = False
        return self._service

    async def list_events(self, calendar_id: str = "primary", max_results: int = 10) -> Dict[str, Any]:
        """List upcoming calendar events."""
        svc = self._get_service()
        if not svc:
            return {"success": False, "error": "Google Calendar not configured."}
        try:
            now = datetime.utcnow().isoformat() + "Z"
            result = (
                svc.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = [
                {
                    "id": e.get("id"),
                    "summary": e.get("summary"),
                    "start": e.get("start"),
                    "end": e.get("end"),
                    "description": e.get("description"),
                    "location": e.get("location"),
                }
                for e in result.get("items", [])
            ]
            return {"success": True, "events": events}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    async def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        calendar_id: str = "primary",
    ) -> Dict[str, Any]:
        """Create a calendar event."""
        svc = self._get_service()
        if not svc:
            return {"success": False, "error": "Google Calendar not configured."}
        try:
            event = {
                "summary": summary,
                "description": description,
                "location": location,
                "start": {"dateTime": start_time, "timeZone": "UTC"},
                "end": {"dateTime": end_time, "timeZone": "UTC"},
            }
            created = svc.events().insert(calendarId=calendar_id, body=event).execute()
            return {"success": True, "event_id": created.get("id"), "link": created.get("htmlLink")}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    async def delete_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Delete a calendar event."""
        svc = self._get_service()
        if not svc:
            return {"success": False, "error": "Google Calendar not configured."}
        try:
            svc.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return {"success": True, "event_id": event_id}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}
