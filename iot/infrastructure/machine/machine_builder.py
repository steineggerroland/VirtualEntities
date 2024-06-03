from iot.infrastructure.exceptions import InvalidThingType
from iot.infrastructure.machine.dishwasher import from_dict as dw_from_dict
from iot.infrastructure.machine.dryer import from_dict as d_from_dict
from iot.infrastructure.machine.machine_that_can_be_loaded import MachineThatCanBeLoaded
from iot.infrastructure.machine.washing_machine import from_dict as wm_from_dict


class MachineBuilder:
    @staticmethod
    def from_dict(entry: dict) -> MachineThatCanBeLoaded:
        if 'type' not in entry:
            raise InvalidThingType()
        if entry['type'] == 'washing_machine':
            return wm_from_dict(entry)
        elif entry['type'] == 'dryer':
            return d_from_dict(entry)
        elif entry['type'] == 'dishwasher':
            return dw_from_dict(entry)
        else:
            raise InvalidThingType(entry['type'])

    @staticmethod
    def can_build(machine_type: str) -> bool:
        return machine_type in ['washing_machine', 'dryer', 'dishwasher']
