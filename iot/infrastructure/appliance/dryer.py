from iot.infrastructure.appliance.appliance_that_can_be_loaded import ApplianceThatCanBeLoaded
from iot.infrastructure.virtual_entity import _datetime_from_dict_key


class Dryer(ApplianceThatCanBeLoaded):
    pass


def from_dict(dictionary: dict):
    return Dryer(dictionary['name'], "dryer", dictionary['watt'] if 'watt' in dictionary else None,
                 _datetime_from_dict_key(dictionary, 'last_updated_at'),
                 dictionary['needs_unloading'] if 'needs_unloading' in dictionary else False,
                 dictionary['is_loaded'] if 'is_loaded' in dictionary else False,
                 _datetime_from_dict_key(dictionary, 'started_run_at'),
                 dictionary['running_state'] if 'running_state' in dictionary else None,
                 _datetime_from_dict_key(dictionary, 'finished_last_run_at'),
                 _datetime_from_dict_key(dictionary, 'last_seen_at'))
