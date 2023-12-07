from datetime import datetime

from iot.machine.IotMachine import _datetime_from_dict_key
from iot.machine.MachineThatCanBeLoaded import MachineThatCanBeLoaded


class Dryer(MachineThatCanBeLoaded):
    pass


def from_dict(dictionary: dict):
    return Dryer(dictionary['name'], dictionary['watt'] if 'watt' in dictionary else None,
                 _datetime_from_dict_key(dictionary, 'last_updated_at'),
                 dictionary['needs_unloading'] if 'needs_unloading' in dictionary else False,
                 dictionary['is_loaded'] if 'is_loaded' in dictionary else False,
                 _datetime_from_dict_key(dictionary, 'started_run_at'),
                 _datetime_from_dict_key(dictionary, 'finished_last_run_at'))

