from enum import Enum

from iot.machine.IotMachine import IotMachine


class PowerState(str, Enum):
    UNKNOWN = 'UNKNOWN'
    OFF = 'OFF'
    IDLE = 'IDLE'
    RUNNING = 'RUNNING'


class SimplePowerStateDecorator:
    def __init__(self, component: IotMachine):
        self.component = component
        self.calculate_simple_state()

    def update_power_consumption(self, watt):
        self.component.watt = watt
        self.calculate_simple_state()

    def calculate_simple_state(self):
        if self.component.watt is None:
            self.component.power_state = PowerState.UNKNOWN
        elif self.component.watt == 0:
            self.component.power_state = PowerState.OFF
        elif self.component.watt < 10:
            self.component.power_state = PowerState.IDLE
        elif self.component.watt >= 10:
            self.component.power_state = PowerState.RUNNING
        else:
            self.component.power_state = PowerState.UNKNOWN
