from datetime import datetime
from enum import Enum


class OnlineStatus(str, Enum):
    UNKNOWN = 'unknown'
    OFFLINE = 'offline'
    ONLINE = 'online'


class IotMachine:
    def __init__(self, name, watt: float | None = None, online_delta_in_seconds=300,
                 last_updated_at: datetime | None = None):
        self.name = name
        self.watt = watt
        self._online_delta_in_seconds = online_delta_in_seconds
        self.last_updated_at = last_updated_at

    def update_power_consumption(self, watt):
        self.watt = watt
        self.last_updated_at = datetime.now()

    def online_status(self):
        if self.last_updated_at is None:
            return OnlineStatus.UNKNOWN
        elif (datetime.now() - self.last_updated_at).total_seconds() <= self._online_delta_in_seconds:
            return OnlineStatus.ONLINE
        else:
            return OnlineStatus.OFFLINE

    def to_dict(self):
        return {"name": self.name, "watt": self.watt, "last_updated_at": self.last_updated_at.isoformat(),
                "online_status": self.online_status()}
