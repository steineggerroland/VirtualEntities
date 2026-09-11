"""Logical hour slots for the board, independent of MQTT and LED wiring."""
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from typing import Iterable
from zoneinfo import ZoneInfo

from iot.infrastructure.time.calendar import Appointment

NORMAL_COLOR = 'ffffff'
IMPORTANT_COLOR = 'ff0000'


def project_day(appointments: Iterable[Appointment], day: date,
                timezone: str = 'Europe/Berlin') -> list[str | None]:
    """Merge repeated local hours and leave nonexistent hours empty.

    All-day events remain available to other consumers but do not occupy slots.
    Importance is the exact, case-sensitive title prefix agreed for the board.
    """
    zone = ZoneInfo(timezone)
    boundaries = set()
    for hour in range(25):
        local = datetime.combine(day, time.min) + timedelta(hours=hour)
        for fold in (0, 1):
            instant = local.replace(tzinfo=zone, fold=fold).astimezone(dt_timezone.utc)
            if instant.astimezone(zone).replace(tzinfo=None) == local:
                boundaries.add(instant)
    boundaries = sorted(boundaries)
    timed = [appointment for appointment in appointments if not appointment.is_all_day]
    slots = [None] * 24
    for start, end in zip(boundaries, boundaries[1:]):
        hour = start.astimezone(zone).hour
        for appointment in timed:
            if appointment.covers_interval(start, end):
                color = IMPORTANT_COLOR if appointment.summary.startswith('Wichtig:') else NORMAL_COLOR
                if slots[hour] != IMPORTANT_COLOR:
                    slots[hour] = color
    return slots
