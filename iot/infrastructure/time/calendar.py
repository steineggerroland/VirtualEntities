from datetime import datetime, timedelta
from typing import List

from iot.infrastructure.thing import Thing


class Appointment:
    def __init__(self, summary: str, start_at: datetime, end_at: datetime):
        self.summary = summary
        self.start_at = start_at
        self.end_at = end_at
        self.last_updated_at = datetime.now()

    def covers_interval(self, start: datetime, end: datetime):
        return not (end < self.start_at or start > self.end_at)

    def to_dict(self):
        return {"summary": self.summary,
                "start_at": self.start_at.isoformat() if self.start_at is not None else None,
                "end_at": self.end_at.isoformat() if self.end_at is not None else None,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None}


class Calendar(Thing):
    def __init__(self, name: str, appointments: List[Appointment] = (), last_updated_at: datetime = datetime.now(),
                 last_seen_at: None | datetime = None):
        super().__init__(name, last_updated_at, last_seen_at, online_delta_in_seconds=60 * 30)
        self.appointments = appointments

    def find_appointments(self, start: datetime, delta: timedelta):
        return list(filter(lambda appointment: appointment.covers_interval(start, start + delta), self.appointments))

    def to_dict(self):
        return {"name": self.name,
                "appointments": list(map(lambda appointment: appointment.to_dict(), self.appointments)),
                "online_status": self.online_status(),
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
