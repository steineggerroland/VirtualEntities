from datetime import datetime
from enum import Enum

from iot.infrastructure.Thing import Thing
from iot.infrastructure.machine.PowerStateDecorator import PowerState, SimplePowerStateDecorator


class OnlineStatus(str, Enum):
    UNKNOWN = 'unknown'
    OFFLINE = 'offline'
    ONLINE = 'online'


class IotMachine(Thing):
    def __init__(self, name, watt: float | None = None, last_updated_at: datetime = datetime.now(),
                 online_delta_in_seconds=300, last_seen_at: None | datetime = None):
        super().__init__(name, last_updated_at, last_seen_at)
        self.watt = watt
        self._online_delta_in_seconds = online_delta_in_seconds
        self.power_state = PowerState.UNKNOWN
        self._power_state_decoration = SimplePowerStateDecorator(self)
        self.started_run_at: datetime | None = None

    def update_power_consumption(self, watt):
        self._power_state_decoration.update_power_consumption(watt)
        now = datetime.now()
        self.last_updated_at = now
        self.last_seen_at = now

    def start_run(self):
        pass

    def finish_run(self):
        pass

    def online_status(self):
        if self.last_seen_at is None:
            return OnlineStatus.UNKNOWN
        if (datetime.now() - self.last_seen_at).total_seconds() <= self._online_delta_in_seconds:
            return OnlineStatus.ONLINE
        return OnlineStatus.OFFLINE

    def to_dict(self):
        return {"name": self.name, "watt": self.watt, "power_state": self.power_state,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "online_status": self.online_status(),
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}


def _datetime_from_dict_key(dictionary: dict, key: str):
    return datetime.fromisoformat(dictionary[key]) if key in dictionary and dictionary[key] is not None else None
