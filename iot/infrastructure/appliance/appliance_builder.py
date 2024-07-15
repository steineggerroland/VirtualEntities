from iot.infrastructure.exceptions import InvalidEntityType
from iot.infrastructure.appliance.dishwasher import from_dict as dw_from_dict
from iot.infrastructure.appliance.dryer import from_dict as d_from_dict
from iot.infrastructure.appliance.appliance_that_can_be_loaded import ApplianceThatCanBeLoaded
from iot.infrastructure.appliance.washing_machine import from_dict as wm_from_dict


class ApplianceBuilder:
    @staticmethod
    def from_dict(entry: dict) -> ApplianceThatCanBeLoaded:
        if 'type' not in entry:
            raise InvalidEntityType()
        if entry['type'] == 'washing_machine':
            return wm_from_dict(entry)
        elif entry['type'] == 'dryer':
            return d_from_dict(entry)
        elif entry['type'] == 'dishwasher':
            return dw_from_dict(entry)
        else:
            raise InvalidEntityType(entry['type'])

    @staticmethod
    def can_build(appliance_type: str) -> bool:
        return appliance_type in ['washing_machine', 'dryer', 'dishwasher']
