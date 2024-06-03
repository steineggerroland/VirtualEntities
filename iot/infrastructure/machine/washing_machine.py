from iot.infrastructure.machine.machine_that_can_be_loaded import MachineThatCanBeLoaded
from iot.infrastructure.thing import _datetime_from_dict_key


class WashingMachine(MachineThatCanBeLoaded):
    pass


def from_dict(dictionary: dict):
    return WashingMachine(dictionary['name'], 'washing_machine', dictionary['watt'] if 'watt' in dictionary else None,
                          _datetime_from_dict_key(dictionary, 'last_updated_at'),
                          dictionary['needs_unloading'] if 'needs_unloading' in dictionary else False,
                          dictionary['is_loaded'] if 'is_loaded' in dictionary else False,
                          _datetime_from_dict_key(dictionary, 'started_run_at'),
                          dictionary['running_state'] if 'running_state' in dictionary else None,
                          _datetime_from_dict_key(dictionary, 'finished_last_run_at'),
                          _datetime_from_dict_key(dictionary, 'last_seen_at'))
