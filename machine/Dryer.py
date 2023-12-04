from machine.IotMachine import IotMachine
from machine.PowerStateDecorator import PowerState, SimplePowerStateDecorator


class Dryer(IotMachine):
    def __init__(self, name, watt=None):
        super().__init__(name, watt)
        self.power_state = PowerState.UNKNOWN
        self._power_state_decoration = SimplePowerStateDecorator(self)

    def update_power_consumption(self, watt):
        self._power_state_decoration.update_power_consumption(watt)


def from_dict(dictionary: dict):
    return Dryer(dictionary['name'], dictionary['watt'] if 'watt' in dictionary else None)
