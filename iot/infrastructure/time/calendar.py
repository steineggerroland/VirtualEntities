from datetime import datetime, timedelta, date
from typing import List

import pytz
from dateutil.tz import tzlocal

from iot.infrastructure.virtual_entity import VirtualEntity


class Appointment:
    def __init__(self, summary: str, start_at: datetime | date, end_at: datetime | date, color: str, description='', timezone: str = 'Europe/Berlin'):
        self.summary = summary
        self.timezone = pytz.timezone(timezone)
        if isinstance(start_at, datetime) != isinstance(end_at, datetime):
            raise ValueError("Appointment boundaries must both be dates or datetimes")
        if not isinstance(start_at, date) or not isinstance(end_at, date):
            raise ValueError("Appointment boundaries must be dates or datetimes")
        self.start_at = self._normalize_time(start_at) if isinstance(start_at, datetime) else start_at
        self.end_at = self._normalize_time(end_at) if isinstance(end_at, datetime) else end_at
        if self.end_at < self.start_at:
            raise ValueError("Appointment end must not precede its start")
        self.color = color.lower()
        self.description = description
        self.last_updated_at = datetime.now(tzlocal())

    @property
    def is_all_day(self) -> bool:
        return not isinstance(self.start_at, datetime)

    def _normalize_time(self, value: datetime) -> datetime:
        # Reject ambiguous/nonexistent floating times rather than using the host timezone.
        return (self.timezone.localize(value, is_dst=None) if value.tzinfo is None
                else value.astimezone(self.timezone))

    def covers_interval(self, start: datetime, end: datetime):
        start, end = self._normalize_time(start), self._normalize_time(end)
        if start >= end or self.start_at == self.end_at:
            return False
        if self.is_all_day:
            appointment_start = self.timezone.localize(datetime.combine(self.start_at, datetime.min.time()))
            appointment_end = self.timezone.localize(datetime.combine(self.end_at, datetime.min.time()))
        else:
            appointment_start, appointment_end = self.start_at, self.end_at
        return appointment_start < end and appointment_end > start

    def to_dict(self):
        return {"summary": self.summary,
                "start_at": self.start_at.isoformat() if self.start_at is not None else None,
                "end_at": self.end_at.isoformat() if self.end_at is not None else None,
                "color": self.color,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None}


class Calendar(VirtualEntity):
    def __init__(self, name: str, url: str, color: str, appointments: List[Appointment] | None = None,
                 last_updated_at: datetime | None = None,
                 last_seen_at: None | datetime = None):
        super().__init__(name, "calendar", last_updated_at if last_updated_at is not None else datetime.now(tzlocal()), last_seen_at, online_delta_in_seconds=60 * 30)
        self.url = url
        self.color = color.lower()
        self.appointments = list(appointments) if appointments is not None else []

    def find_appointments(self, start: datetime, delta: timedelta):
        return list(filter(lambda appointment: appointment.covers_interval(start, start + delta), self.appointments))

    def to_dict(self):
        return {"name": self.name,
                "url": self.url,
                "appointments": list(map(lambda appointment: appointment.to_dict(), self.appointments)),
                "color": self.color,
                "online_status": self.online_status(),
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
