from datetime import datetime, timedelta
from functools import reduce
from typing import List

from dateutil.tz import tzlocal

from iot.infrastructure.time.calendar import Calendar, Appointment
from iot.infrastructure.virtual_entity import VirtualEntity


class Person(VirtualEntity):
    def __init__(self, name: str, calendars: List[Calendar] = (), last_updated_at: datetime = datetime.now(tzlocal()),
                 last_seen_at: None | datetime = None):
        super().__init__(name, "person", last_updated_at, last_seen_at, online_delta_in_seconds=60 * 10)
        self.calendars = calendars

    def set_calendars(self, calendars) -> 'Person':
        now = datetime.now(tzlocal())
        return Person(self.name, calendars, now, now)

    def change_name(self, name) -> 'Person':
        return Person(name, self.calendars, datetime.now(tzlocal()), self.last_seen_at)

    def get_appointments_for(self, start: datetime, delta: timedelta) -> List[Appointment]:
        return list(reduce(lambda a, b: a + b, map(lambda c: c.find_appointments(start, delta), self.calendars), []))

    def get_n_upcoming_appointments(self, n: int) -> List[Appointment]:
        all_appointments = reduce(lambda a, b: a + b, map(lambda c: c.appointments, self.calendars), [])
        all_appointments.sort(key=lambda a: a.start_at)
        return list(all_appointments)[:n]

    def to_dict(self):
        return {"name": self.name,
                "calendars": list(map(lambda c: c.to_dict(), self.calendars)),
                "online_status": self.online_status(),
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
