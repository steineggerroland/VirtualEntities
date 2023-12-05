from datetime import datetime

from iot.machine.IotMachine import IotMachine
from iot.machine.PowerStateDecorator import PowerState, SimplePowerStateDecorator


class Dryer(IotMachine):
    def __init__(self, name, watt: float | None = None, last_updated_at: datetime | None = None):
        super().__init__(name, watt, last_updated_at=last_updated_at)
        self.power_state = PowerState.UNKNOWN
        self._power_state_decoration = SimplePowerStateDecorator(self)

    def update_power_consumption(self, watt):
        self._power_state_decoration.update_power_consumption(watt)
        self.last_updated_at = datetime.now()

    def to_dict(self):
        return {"name": self.name, "watt": self.watt, "power_state": self.power_state,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "online_status": self.online_status()}


def from_dict(dictionary: dict):
    return Dryer(dictionary['name'], dictionary['watt'] if 'watt' in dictionary else None,
                 datetime.fromisoformat(
                     dictionary['last_updated_at']) if 'last_updated_at' in dictionary else None)
