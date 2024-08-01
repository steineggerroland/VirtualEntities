from iot.infrastructure.appliance.appliance import BasicAppliance
from iot.infrastructure.appliance.appliance_enhancements import LoadableAppliance
from iot.infrastructure.exceptions import InvalidEntityType
from iot.infrastructure.virtual_entity import _datetime_from_dict_key
from project import Project


class ApplianceBuilder:
    @staticmethod
    def build_with(**kwargs) -> BasicAppliance | LoadableAppliance:
        appliance = BasicAppliance(name=kwargs['name'], entity_type=kwargs['type'],
                                   watt=kwargs.get('watt', None),
                                   watt_threshold=kwargs.get('watt_threshold', None),
                                   power_consumption_indicates_charging=kwargs.get('power_consumption_indicates_charging',
                                                                                  None),
                                   running_state=kwargs.get('running_state', None),
                                   started_run_at=kwargs.get('started_run_at', None),
                                   last_updated_at=kwargs.get('last_updated_at', None),
                                   online_delta_in_seconds=kwargs.get('online_delta_in_seconds', None),
                                   finished_last_run_at=kwargs.get('finished_last_run_at', None),
                                   last_seen_at=kwargs.get('last_seen_at', None))
        if 'is_loadable' in kwargs and kwargs['is_loadable']:
            appliance = LoadableAppliance(appliance,
                                          is_loaded=kwargs['is_loaded'] if 'is_loaded' in kwargs else None,
                                          needs_unloading=kwargs[
                                              'needs_unloading'] if 'needs_unloading' in kwargs else None)
        return appliance

    @staticmethod
    def from_dict(dictionary: dict) -> BasicAppliance | LoadableAppliance:
        if 'type' not in dictionary or not ApplianceBuilder.can_build(dictionary['type']):
            raise InvalidEntityType()
        is_loadable = dictionary['is_loadable'] if 'is_loadable' in dictionary else (
                'needs_unloading' in dictionary or 'is_loaded' in dictionary)
        return ApplianceBuilder.build_with(name=dictionary['name'], type=dictionary['type'],
                                           watt=dictionary['watt'] if 'watt' in dictionary else None,
                                           last_updated_at=_datetime_from_dict_key(dictionary, 'last_updated_at'),
                                           watt_threshold=dictionary[
                                               'watt_threshold'] if 'watt_threshold' in dictionary else None,
                                           power_consumption_indicates_charging=dictionary[
                                               'power_consumption_indicates_charging'] if 'power_consumption_indicates_charging' in dictionary else None,
                                           started_run_at=_datetime_from_dict_key(dictionary, 'started_run_at'),
                                           running_state=dictionary[
                                               'running_state'] if 'running_state' in dictionary else None,
                                           finished_last_run_at=_datetime_from_dict_key(dictionary,
                                                                                        'finished_last_run_at'),
                                           last_seen_at=_datetime_from_dict_key(dictionary, 'last_seen_at'),
                                           is_loadable=is_loadable,
                                           needs_unloading=dictionary[
                                               'needs_unloading'] if 'needs_unloading' in dictionary else False,
                                           is_loaded=dictionary['is_loaded'] if 'is_loaded' in dictionary else False
                                           )

    @staticmethod
    def make_loadable(appliance):
        appliance = ApplianceBuilder.from_dict(appliance.to_dict())
        return LoadableAppliance(appliance)

    @staticmethod
    def can_build(appliance_type: str) -> bool:
        return appliance_type in Project.appliance_types_that_can_be_loaded
