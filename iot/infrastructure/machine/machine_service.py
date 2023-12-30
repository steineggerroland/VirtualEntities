import logging
import time
from threading import Thread

from iot.core.configuration import IotThingConfig
from iot.core.storage import Storage
from iot.infrastructure.exceptions import DatabaseException, InvalidThingType
from iot.infrastructure.machine.dishwasher import from_dict as dw_from_dict
from iot.infrastructure.machine.dryer import from_dict as d_from_dict
from iot.infrastructure.machine.power_state_decorator import PowerState
from iot.infrastructure.machine.run_complete_strategy import SimpleHistoryRunCompleteStrategy
from iot.infrastructure.machine.washing_machine import from_dict as wm_from_dict


class MachineService:
    def __init__(self, storage: Storage, thing_config: IotThingConfig):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.storage = storage
        db_entry = self.storage.load_thing(thing_config.name)
        if thing_config.type == 'washing_machine':
            self.thing = wm_from_dict(db_entry)
        elif thing_config.type == 'dryer':
            self.thing = d_from_dict(db_entry)
        elif thing_config.type == 'dishwasher':
            self.thing = dw_from_dict(db_entry)
        else:
            raise InvalidThingType(thing_config)
        self.run_complete_strategy = SimpleHistoryRunCompleteStrategy(storage)
        if self.thing.started_run_at is not None:
            self.started_run()

    def update_power_consumption(self, new_power_consumption):
        try:
            self.thing.update_power_consumption(new_power_consumption)
            self.storage.update_thing(self.thing)
            self.storage.append_power_consumption(new_power_consumption, self.thing.name)
            if self.thing.started_run_at is None and self.thing.power_state is PowerState.RUNNING:
                self.started_run()
        except ValueError as e:
            raise DatabaseException('Failed to save new power consumption because of database error.', e) from e

    def started_run(self):
        try:
            if not self.thing.start_run:
                return
            self.thing.start_run()
            self.storage.update_thing(self.thing)
            check_if_run_completed_thread = Thread(target=self._scheduled_check, daemon=True)
            check_if_run_completed_thread.start()
        except ValueError as e:
            raise DatabaseException('Failed to save started run because of database error.', e) from e

    def _scheduled_check(self):
        while not self.run_complete_strategy.is_run_completed(self.thing):
            time.sleep(10)
        try:
            self.finished_run()
        except DatabaseException as e:
            self.logger.error("Failed to finish run of '%s' because of database error.", self.thing.name, exc_info=e)

    def finished_run(self):
        try:
            self.thing.finish_run()
            self.storage.update_thing(self.thing)
        except ValueError as e:
            raise DatabaseException('Failed to save finished run because of database error.', e) from e

    def unloaded(self):
        try:
            self.thing.unload()
            self.storage.update_thing(self.thing)
        except ValueError as e:
            raise DatabaseException('Failed to save unloading machine because of database error.', e) from e

    def loaded(self, needs_unloading=False):
        try:
            self.thing.load(needs_unloading)
            self.storage.update_thing(self.thing)
        except ValueError as e:
            raise DatabaseException('Failed to save setting machine to loaded.', e) from e


def supports_thing_type(thing_type) -> bool:
    return thing_type in ['washing_machine', 'dryer', 'dishwasher']
