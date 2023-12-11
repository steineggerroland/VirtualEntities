import logging
import time
from threading import Thread

from iot.core.Storage import Storage
from iot.core.configuration import IotThingConfig
from iot.machine.Dryer import from_dict as d_from_dict
from iot.machine.PowerStateDecorator import PowerState
from iot.machine.WashingMachine import from_dict as wm_from_dict


class MachineService:
    def __init__(self, storage: Storage, thing_config: IotThingConfig):
        self.storage = storage
        db_entry = self.storage.load_thing(thing_config.name)
        if thing_config.type == 'washing_machine':
            self.thing = wm_from_dict(db_entry)
        elif thing_config.type == 'dryer':
            self.thing = d_from_dict(db_entry)
        else:
            raise InvalidThingType(thing_config)
        self.logger = logging.getLogger(self.__class__.__qualname__)
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
            if self.thing.start_run:
                self.thing.start_run()
                self.storage.update_thing(self.thing)
                check_if_run_completed_thread = Thread(target=self._scheduled_check, daemon=True)
                check_if_run_completed_thread.start()
        except ValueError as e:
            raise DatabaseException('Failed to save started run because of database error.', e) from e

    def _scheduled_check(self):
        while not self._run_completed():
            time.sleep(10)
        try:
            self.finished_run()
        except DatabaseException as e:
            self.logger.error("Failed to finish run of '%s' because of database error.", self.thing.name, exc_info=e)

    def _run_completed(self):
        if self.thing.power_state is PowerState.RUNNING:
            return False
        power_consumptions = self.storage.get_power_consumptions_for_last_seconds(150, self.thing.name)
        if any(power_consumption['watt'] > 10 for power_consumption in power_consumptions):
            return False
        return True

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

    def loaded(self):
        try:
            self.thing.load()
            self.storage.update_thing(self.thing)
        except ValueError as e:
            raise DatabaseException('Failed to save setting machine to loaded.', e) from e


class DatabaseException(Exception):
    def __init__(self, msg: str, cause: Exception | None = None):
        self.msg = msg
        self.cause = cause


class InvalidThingType(Exception):
    def __init__(self, thing_config: IotThingConfig):
        self.msg = "thing type '%s' is unknown" % thing_config.type
