from datetime import datetime, timedelta

from iot.infrastructure.appliance.power_state_decorator import PowerState, SimplePowerStateDecorator
from iot.infrastructure.virtual_entity import VirtualEntity


class Appliance(VirtualEntity):
    def __init__(self, name, entity_type: str, watt: float | None = None, last_updated_at: datetime = datetime.now(),
                 online_delta_in_seconds=300, started_last_run_at=None, finished_last_run_at=None,
                 last_seen_at: None | datetime = None):
        super().__init__(name, entity_type, last_updated_at, last_seen_at, online_delta_in_seconds)
        self.watt = watt
        self.power_state = PowerState.UNKNOWN
        self._power_state_decoration = SimplePowerStateDecorator(self)
        self.started_run_at: datetime | None = started_last_run_at
        self.finished_last_run_at: datetime | None = finished_last_run_at

    def update_power_consumption(self, watt):
        self._power_state_decoration.update_power_consumption(watt)
        now = datetime.now()
        self.last_updated_at = now
        self.last_seen_at = now

    def start_run(self):
        now = datetime.now()
        self.started_run_at = now
        self.last_updated_at = now

    def finish_run(self):
        self.started_run_at = None
        now = datetime.now()
        self.finished_last_run_at = now
        self.last_updated_at = now

    def rename(self, name: str):
        self.name = name
        now = datetime.now()
        self.last_updated_at = now

    def running_for_time_period(self) -> timedelta:
        if self.started_run_at is not None:
            return self.started_run_at - datetime.now()
        else:
            return timedelta(0)

    def finished_last_run_before_time_period(self) -> timedelta:
        if self.finished_last_run_at is not None:
            return self.finished_last_run_at - datetime.now()
        else:
            return timedelta(0)

    def to_dict(self):
        return {"name": self.name, "type": self.entity_type, "watt": self.watt, "power_state": self.power_state,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "online_status": self.online_status(),
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
