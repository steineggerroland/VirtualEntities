from datetime import datetime
from enum import Enum

from iot.infrastructure.machine.iot_machine import IotMachine


class RunningState(str, Enum):
    UNKNOWN = 'unknown'
    IDLE = 'idle'
    RUNNING = 'running'


class MachineThatCanBeLoaded(IotMachine):
    def __init__(self, name, watt: float | None = None, last_updated_at: datetime | None = None, needs_unloading=False,
                 is_loaded=False, started_last_run_at=None, running_state=None,
                 finished_last_run_at=None,
                 last_seen_at: None | datetime = None):
        super().__init__(name, watt, last_updated_at=last_updated_at, last_seen_at=last_seen_at,
                         started_last_run_at=started_last_run_at, finished_last_run_at=finished_last_run_at)
        self.needs_unloading = needs_unloading
        self.is_loaded = is_loaded or needs_unloading
        self.running_state = running_state if running_state else RunningState.UNKNOWN

    def unload(self):
        self.needs_unloading = False
        self.is_loaded = False
        self.last_updated_at = datetime.now()

    def load(self, needs_unloading=False):
        self.is_loaded = True
        self.needs_unloading = needs_unloading
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
                                    "running_state": self.running_state,
                                    "finished_last_run_at": self.finished_last_run_at.isoformat() if self.finished_last_run_at is not None else None, }
