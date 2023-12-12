from datetime import datetime

from iot.infrastructure.machine.IotMachine import IotMachine


class MachineThatCanBeLoaded(IotMachine):
    def __init__(self, name, watt: float | None = None, last_updated_at: datetime | None = None, needs_unloading=False,
                 is_loaded=False, started_last_run_at=None, finished_last_run_at=None,
                 last_seen_at: None | datetime = None):
        super().__init__(name, watt, last_updated_at=last_updated_at, last_seen_at=last_seen_at)
        self.needs_unloading = needs_unloading
        self.is_loaded = is_loaded or needs_unloading
        self.started_run_at: datetime | None = started_last_run_at
        self.finished_last_run_at: datetime | None = finished_last_run_at

    def unload(self):
        self.needs_unloading = False
        self.is_loaded = False
        self.last_updated_at = datetime.now()

    def load(self):
        self.is_loaded = True
        self.last_updated_at = datetime.now()

    def start_run(self):
        self.is_loaded = True
        self.needs_unloading = False
        self.started_run_at = datetime.now()
        self.last_updated_at = datetime.now()

    def finish_run(self):
        if self.is_loaded:
            self.needs_unloading = True
        self.started_run_at = None
        self.finished_last_run_at = datetime.now()
        self.last_updated_at = datetime.now()

    def to_dict(self):
        return super().to_dict() | {"is_loaded": self.is_loaded, "needs_unloading": self.needs_unloading,
                                    "started_run_at": self.started_run_at.isoformat() if self.started_run_at is not None else None,
                                    "finished_last_run_at": self.finished_last_run_at.isoformat() if self.finished_last_run_at is not None else None, }
