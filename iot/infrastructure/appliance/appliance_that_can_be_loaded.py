import logging
from datetime import datetime
from enum import Enum

from iot.infrastructure.appliance.appliance import Appliance
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.virtual_entity import _datetime_from_dict_key


class RunningState(str, Enum):
    UNKNOWN = 'unknown'
    IDLE = 'idle'
    RUNNING = 'running'


class ApplianceThatCanBeLoaded(Appliance):
    def __init__(self, name, entity_type: str, watt: float | None = None, last_updated_at: datetime | None = None,
                 needs_unloading=False,
                 is_loaded=False, started_last_run_at=None, running_state=None,
                 finished_last_run_at=None,
                 last_seen_at: None | datetime = None):
        super().__init__(name, entity_type, watt, last_updated_at=last_updated_at, last_seen_at=last_seen_at,
                         started_last_run_at=started_last_run_at, finished_last_run_at=finished_last_run_at)
        self.needs_unloading = needs_unloading
        self.is_loaded = is_loaded or needs_unloading
        self.running_state = running_state if running_state else RunningState.UNKNOWN

    def update_power_consumption(self, watt):
        super().update_power_consumption(watt)
        if self.running_state == RunningState.UNKNOWN and self.power_state == PowerState.OFF:
            self.running_state = RunningState.IDLE
        elif self.running_state == RunningState.UNKNOWN and self.power_state == PowerState.RUNNING:
            self.running_state = RunningState.RUNNING

    def unload(self):
        self.needs_unloading = False
        self.is_loaded = False
        self.last_updated_at = datetime.now()

    def load(self, needs_unloading=False):
        self.is_loaded = True
        self.needs_unloading = needs_unloading if not self.running_state == RunningState.RUNNING else False
        self.last_updated_at = datetime.now()

    def start_run(self):
        super().start_run()
        self.is_loaded = True
        self.needs_unloading = False
        self.running_state = RunningState.RUNNING

    def finish_run(self):
        super().finish_run()
        if self.is_loaded:
            self.needs_unloading = True
        self.running_state = RunningState.IDLE

    def to_dict(self):
        return super().to_dict() | {"is_loaded": self.is_loaded, "needs_unloading": self.needs_unloading,
                                    "started_run_at": self.started_run_at.isoformat() if self.started_run_at is not None else None,
                                    "running_state": self.running_state if type(self.running_state) is str else self.running_state.value,
                                    "finished_last_run_at": self.finished_last_run_at.isoformat() if self.finished_last_run_at is not None else None, }

    @staticmethod
    def from_dict(dictionary: dict):
        return ApplianceThatCanBeLoaded(dictionary['name'], dictionary['type'],
                                        dictionary['watt'] if 'watt' in dictionary else None,
                                        _datetime_from_dict_key(dictionary, 'last_updated_at'),
                                        dictionary['needs_unloading'] if 'needs_unloading' in dictionary else False,
                                        dictionary['is_loaded'] if 'is_loaded' in dictionary else False,
                                        _datetime_from_dict_key(dictionary, 'started_run_at'),
                                        dictionary['running_state'] if 'running_state' in dictionary else None,
                                        _datetime_from_dict_key(dictionary, 'finished_last_run_at'),
                                        _datetime_from_dict_key(dictionary, 'last_seen_at'))