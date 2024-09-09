from datetime import datetime

from dateutil.tz import tzlocal


class Run:
    def __init__(self, started_at, finished_at: datetime | None = None):
        self.started_at = started_at
        self.finished_at = finished_at
        self.duration = finished_at - started_at if finished_at is not None else datetime.now(tzlocal()) - started_at
    def to_dict(self) -> dict:
        return {
            'started_at': self.started_at.isoformat(),
            'finished_at': self.finished_at.isoformat(),
            'duration_s': self.duration.total_seconds(),
        }
