from enum import Enum


class PowerState(str, Enum):
    UNKNOWN = 'unknown'
    OFF = 'offline'
    IDLE = 'idle'
    RUNNING = 'running'


class SimplePowerStateDecorator:
    def __init__(self, component, watt_threshold):
        self.component = component
        self.watt_threshold = watt_threshold if watt_threshold is not None else 10
        self.calculate_simple_state()

    def update_power_consumption(self, watt):
        self.component.watt = watt
        self.calculate_simple_state()

    def calculate_simple_state(self):
        if self.component.watt is None:
            self.component.power_state = PowerState.UNKNOWN
        elif self.component.watt == 0:
            self.component.power_state = PowerState.OFF
        elif self.component.watt < self.watt_threshold:
            self.component.power_state = PowerState.IDLE
        elif self.component.watt >= self.watt_threshold:
            self.component.power_state = PowerState.RUNNING
        else:
            self.component.power_state = PowerState.UNKNOWN
