from datetime import datetime

from iot.machine.PowerStateMachine import PowerStateMachine


class WashingMachine(PowerStateMachine):
    pass


def from_dict(dictionary: dict):
    return WashingMachine(dictionary['name'], dictionary['watt'] if 'watt' in dictionary else None,
                          datetime.fromisoformat(
                              dictionary['last_updated_at']) if 'last_updated_at' in dictionary else None)
