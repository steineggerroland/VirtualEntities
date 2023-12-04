from iot.core.configuration import Configuration
from iot.core.Storage import Storage
from iot.machine.Dryer import from_dict as d_from_dict
from iot.machine.WashingMachine import from_dict as wm_from_dict


class MachineService:
    def __init__(self, storage: Storage, config: Configuration):
        self.storage = storage
        db_entry = self.storage.load_thing(config.name)
        if config.type == 'washing_machine':
            self.thing = wm_from_dict(db_entry)
        elif config.type == 'dryer':
            self.thing = d_from_dict(db_entry)

    def update_power_consumption(self, new_power_consumption):
        self.thing.update_power_consumption(new_power_consumption)
        self.storage.update_thing(self.thing)
        self.storage.append_power_consumption(new_power_consumption, self.thing)
