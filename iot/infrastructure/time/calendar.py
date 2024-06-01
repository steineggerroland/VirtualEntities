from datetime import datetime, timedelta, date
from typing import List

import pytz

from iot.infrastructure.thing import Thing


class Appointment:
    def __init__(self, summary: str, start_at: datetime | date, end_at: datetime | date, color: str):
        self.summary = summary
        self.start_at = start_at.astimezone(pytz.timezone("Europe/Berlin"))
        self.end_at = end_at.astimezone(pytz.timezone("Europe/Berlin"))
        self.color = color.lower()
        self.last_updated_at = datetime.now()

    def covers_interval(self, start: datetime, end: datetime):
        if (type(self.start_at) is not datetime and type(self.start_at) is not date) or \
                (type(self.end_at) is not datetime and type(self.end_at) is not date):
            return False
        if start.tzname() is None:
            start = start.astimezone(pytz.timezone("Europe/Berlin"))
        if end.tzname() is None:
            end = end.astimezone(pytz.timezone("Europe/Berlin"))
        start = start if type(self.end_at) is datetime else date(start.year, start.month, start.day)
        end = end if type(self.start_at) is datetime else date(end.year, end.month, end.day)
        return not (end < self.start_at or start > self.end_at)

    def to_dict(self):
        return {"summary": self.summary,
                "start_at": self.start_at.isoformat() if self.start_at is not None else None,
                "end_at": self.end_at.isoformat() if self.end_at is not None else None,
                "color": self.color,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None}


class Calendar(Thing):
    def __init__(self, name: str, url: str, color: str, appointments: List[Appointment] = [],
                 last_updated_at: datetime = datetime.now(),
                 last_seen_at: None | datetime = None):
        super().__init__(name, "calendar", last_updated_at, last_seen_at, online_delta_in_seconds=60 * 30)
        self.url = url
        self.color = color.lower()
        self.appointments = appointments

    def find_appointments(self, start: datetime, delta: timedelta):
        start = start if start.tzname() is not None else start.astimezone(pytz.timezone("Europe/Berlin"))
        return list(filter(lambda appointment: appointment.covers_interval(start, start + delta), self.appointments))

    def to_dict(self):
        return {"name": self.name,
                "url": self.url,
                "appointments": list(map(lambda appointment: appointment.to_dict(), self.appointments)),
                "color": self.color,
                "online_status": self.online_status(),
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
