from datetime import datetime

from iot.infrastructure.machine.power_state_decorator import PowerState, SimplePowerStateDecorator
from iot.infrastructure.thing import Thing


class IotMachine(Thing):
    def __init__(self, name, watt: float | None = None, last_updated_at: datetime = datetime.now(),
                 online_delta_in_seconds=300, last_seen_at: None | datetime = None):
        super().__init__(name, last_updated_at, last_seen_at, online_delta_in_seconds)
        self.watt = watt
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

    def to_dict(self):
        return {"name": self.name, "watt": self.watt, "power_state": self.power_state,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "online_status": self.online_status(),
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
