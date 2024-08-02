import abc
from datetime import datetime, timedelta
from enum import Enum

from dateutil.tz import tzlocal

from iot.infrastructure.appliance.power_state_decorator import PowerState, SimplePowerStateDecorator
from iot.infrastructure.virtual_entity import VirtualEntity, BaseVirtualEntity


class RunningState(str, Enum):
    UNKNOWN = 'unknown'
    IDLE = 'idle'
    RUNNING = 'running'
    LOADING = 'loading'


class Appliance(BaseVirtualEntity, metaclass=abc.ABCMeta):
    watt: float
    power_state: PowerState
    running_state: RunningState
    power_consumption_indicates_charging: bool
    started_run_at: datetime | None
    finished_last_run_at: datetime | None

    @abc.abstractmethod
    def update_power_consumption(self, watt: float) -> 'Appliance':
        return self

    @abc.abstractmethod
    def start_run(self) -> 'Appliance':
        return self

    @abc.abstractmethod
    def finish_run(self) -> 'Appliance':
        return self

    @abc.abstractmethod
    def rename(self, name: str) -> 'Appliance':
        return self

    @abc.abstractmethod
    def running_for_time_period(self) -> datetime:
        pass

    @abc.abstractmethod
    def finished_last_run_before_time_period(self) -> timedelta:
        pass

    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass


class BasicAppliance(Appliance, VirtualEntity):
    def __init__(self, name, entity_type: str, watt: float | None = None,
                 watt_threshold: float | None = None, power_consumption_indicates_charging=None,
                 running_state=RunningState.UNKNOWN,
                 last_updated_at: datetime|None = datetime.now(tzlocal()),
                 online_delta_in_seconds=300, started_run_at=None, finished_last_run_at=None,
                 last_seen_at: None | datetime = None):
        VirtualEntity.__init__(self, name, entity_type, last_updated_at, last_seen_at, online_delta_in_seconds)
        self.watt = watt
        self.power_state = PowerState.UNKNOWN
        self.running_state = running_state if running_state is not None else RunningState.UNKNOWN
        self.started_run_at: datetime | None = started_run_at.astimezone(
            tzlocal()) if started_run_at and not power_consumption_indicates_charging else None
        self.finished_last_run_at: datetime | None = finished_last_run_at.astimezone(
            tzlocal()) if finished_last_run_at else None
        self.power_consumption_indicates_charging = power_consumption_indicates_charging if power_consumption_indicates_charging is not None else False
        self._power_state_decoration = SimplePowerStateDecorator(self, watt_threshold)

        # if power consumption indicates charging, then there is no knowledge about runs
        self.started_run_at = None if power_consumption_indicates_charging else self.started_run_at
        self.running_state = RunningState.UNKNOWN if power_consumption_indicates_charging and running_state == RunningState.RUNNING else self.running_state

    def update_power_consumption(self, watt):
        self._power_state_decoration.update_power_consumption(watt)
        if (self.running_state == RunningState.UNKNOWN) and (self.power_state == PowerState.OFF or
                                                             self.power_state == PowerState.CHARGING):
            self.running_state = RunningState.IDLE
        elif self.running_state == RunningState.UNKNOWN and self.power_state == PowerState.RUNNING:
            self.running_state = RunningState.RUNNING
        now = datetime.now(tzlocal())
        self.last_updated_at = now
        self.last_seen_at = now
        return self

    def start_run(self):
        now = datetime.now(tzlocal())
        self.started_run_at = now
        self.last_updated_at = now
        self.running_state = RunningState.RUNNING
        return self

    def finish_run(self):
        self.started_run_at = None
        now = datetime.now(tzlocal())
        self.finished_last_run_at = now
        self.last_updated_at = now
        self.running_state = RunningState.IDLE
        return self

    def rename(self, name: str):
        self.name = name
        now = datetime.now(tzlocal())
        self.last_updated_at = now
        return self

    def running_for_time_period(self) -> timedelta:
        if self.started_run_at is not None:
            return self.started_run_at - datetime.now(tzlocal())
        else:
            return timedelta(0)

    def finished_last_run_before_time_period(self) -> timedelta:
        if self.finished_last_run_at is not None:
            return self.finished_last_run_at - datetime.now(tzlocal())
        else:
            return timedelta(0)

    def to_dict(self):
        return {"name": self.name, "type": self.entity_type, "watt": self.watt,
                "power_state": self.power_state if type(self.power_state) is str else self.power_state.value,
                "started_run_at": self.started_run_at.isoformat() if self.started_run_at is not None else None,
                "running_state": self.running_state if type(
                    self.running_state) is str else self.running_state.value,
                'power_consumption_indicates_charging': self.power_consumption_indicates_charging,
                "finished_last_run_at": self.finished_last_run_at.isoformat() if self.finished_last_run_at is not None else None,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "online_status": self.online_status() if type(
                    self.online_status()) is str else self.online_status().value,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
