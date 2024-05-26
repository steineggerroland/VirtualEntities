import logging
import time
from threading import Thread

from iot.core.configuration import IotThingConfig
from iot.core.storage import Storage
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.machine.power_state_decorator import PowerState
from iot.infrastructure.machine.run_complete_strategy import SimpleHistoryRunCompleteStrategy


class MachineService:
    def __init__(self, storage: Storage, thing_config: IotThingConfig):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.storage = storage
        self.machine_name = thing_config.name
        db_entry = self.storage.load_iot_machine(thing_config.name)
        self.run_complete_strategy = SimpleHistoryRunCompleteStrategy(storage)
        if db_entry.started_run_at is not None:
            self.started_run()

    def update_power_consumption(self, new_power_consumption):
        try:
            machine = self.storage.load_iot_machine(self.machine_name)
            machine.update_power_consumption(new_power_consumption)
            self.storage.update_thing(machine)
            self.storage.append_power_consumption(new_power_consumption, machine.name)
            if machine.started_run_at is None and machine.power_state is PowerState.RUNNING:
                self.started_run()
        except ValueError as e:
            raise DatabaseException('Failed to save new power consumption because of database error.', e) from e

    def started_run(self):
        try:
            machine = self.storage.load_iot_machine(self.machine_name)
            if not machine.start_run:
                return
            machine.start_run()
            self.storage.update_thing(machine)
            check_if_run_completed_thread = Thread(target=self._scheduled_check, daemon=True)
            check_if_run_completed_thread.start()
        except ValueError as e:
            raise DatabaseException('Failed to save started run because of database error.', e) from e

    def _scheduled_check(self):
        machine = self.storage.load_iot_machine(self.machine_name)
        while not self.run_complete_strategy.is_run_completed(machine):
            time.sleep(10)
            machine = self.storage.load_iot_machine(self.machine_name)
        try:
            self.finished_run()
        except DatabaseException as e:
            self.logger.error("Failed to finish run of '%s' because of database error.", machine.name, exc_info=e)

    def finished_run(self):
        try:
            machine = self.storage.load_iot_machine(self.machine_name)
            machine.finish_run()
            self.storage.update_thing(machine)
        except ValueError as e:
            raise DatabaseException('Failed to save finished run because of database error.', e) from e

    def unloaded(self):
        try:
            machine = self.storage.load_iot_machine(self.machine_name)
            machine.unload()
            self.storage.update_thing(machine)
        except ValueError as e:
            raise DatabaseException('Failed to save unloading machine because of database error.', e) from e

    def loaded(self, needs_unloading=False):
        try:
            machine = self.storage.load_iot_machine(self.machine_name)
            machine.load(needs_unloading)
            self.storage.update_thing(machine)
        except ValueError as e:
            raise DatabaseException('Failed to save setting machine to loaded.', e) from e


def supports_thing_type(thing_type) -> bool:
    return thing_type in ['washing_machine', 'dryer', 'dishwasher']
