import abc
from datetime import datetime, timedelta

from dateutil.tz import tzlocal

from iot.infrastructure.appliance.appliance import BasicAppliance, Appliance, RunningState
from iot.infrastructure.virtual_entity import OnlineStatus


class ApplianceEnhancement(Appliance, metaclass=abc.ABCMeta):

    def __init__(self, appliance: BasicAppliance):
        self.wrapped_appliance = appliance

    @property
    def name(self):
        return self.wrapped_appliance.name

    @property
    def entity_type(self):
        return self.wrapped_appliance.entity_type

    @property
    def last_updated_at(self):
        return self.wrapped_appliance.last_updated_at

    @property
    def last_seen_at(self):
        return self.wrapped_appliance.last_seen_at

    @property
    def watt(self):
        return self.wrapped_appliance.watt

    @property
    def power_state(self):
        return self.wrapped_appliance.power_state

    @property
    def running_state(self):
        return self.wrapped_appliance.running_state

    @property
    def started_run_at(self):
        return self.wrapped_appliance.started_run_at

    @property
    def finished_last_run_at(self):
        return self.wrapped_appliance.finished_last_run_at

    @property
    def power_consumption_indicates_charging(self):
        return self.wrapped_appliance.power_consumption_indicates_charging

    @entity_type.setter
    def entity_type(self, value):
        self.wrapped_appliance.entity_type = value

    @last_updated_at.setter
    def last_updated_at(self, value):
        self.wrapped_appliance.last_updated_at = value

    @last_seen_at.setter
    def last_seen_at(self, value):
        self.wrapped_appliance.last_seen_at = value

    @watt.setter
    def watt(self, value):
        self.wrapped_appliance.watt = value

    @power_state.setter
    def power_state(self, value):
        self.wrapped_appliance.power_state = value

    @running_state.setter
    def running_state(self, value):
        self.wrapped_appliance.running_state = value

    @started_run_at.setter
    def started_run_at(self, value):
        self.wrapped_appliance.started_run_at = value

    @finished_last_run_at.setter
    def finished_last_run_at(self, value):
        self.wrapped_appliance.finished_last_run_at = value

    @power_consumption_indicates_charging.setter
    def power_consumption_indicates_charging(self, value):
        self.wrapped_appliance.power_consumption_indicates_charging = value

    def wrapped_appliance(self):
        return self.wrapped_appliance

    def update_power_consumption(self, watt) -> 'Appliance':
        self.wrapped_appliance.update_power_consumption(watt)
        return self

    def start_run(self) -> 'Appliance':
        self.wrapped_appliance.start_run()
        return self

    def finish_run(self) -> 'Appliance':
        self.wrapped_appliance.finish_run()
        return self

    def rename(self, name) -> 'Appliance':
        self.wrapped_appliance.rename(name)
        return self

    def running_for_time_period(self) -> timedelta:
        return self.wrapped_appliance.running_for_time_period()

    def finished_last_run_before_time_period(self) -> timedelta:
        return self.wrapped_appliance.finished_last_run_before_time_period()

    def to_dict(self) -> dict:
        return self.wrapped_appliance.to_dict()

    def online_status(self) -> OnlineStatus:
        return self.wrapped_appliance.online_status()

    def last_seen_time_delta(self) -> timedelta | None:
        return self.wrapped_appliance.last_seen_time_delta()


class LoadableAppliance(ApplianceEnhancement):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load') and
                callable(subclass.load) and
                hasattr(subclass, 'unload') and
                callable(subclass.unload) and
                hasattr(subclass, 'is_loaded') and
                hasattr(subclass, 'needs_unloading') or
                NotImplemented)

    def __init__(self, appliance_to_enhance: BasicAppliance, is_loaded=None, needs_unloading=None):
        super().__init__(appliance_to_enhance)
        self.is_loaded = is_loaded if is_loaded is not None else False
        self.needs_unloading = needs_unloading if needs_unloading is not None else False
        self.is_loadable = True

    def unload(self):
        self.needs_unloading = False
        self.is_loaded = False
        ApplianceEnhancement.wrapped_appliance(self).last_updated_at = datetime.now(tzlocal())
        return self

    def load(self, needs_unloading=False):
        self.is_loaded = True
        self.needs_unloading = needs_unloading if not ApplianceEnhancement.wrapped_appliance(
            self).running_state == RunningState.RUNNING else False
        ApplianceEnhancement.wrapped_appliance(self).last_updated_at = datetime.now(tzlocal())
        return self

    def start_run(self):
        super().start_run()
        self.is_loaded = True
        self.needs_unloading = False
        ApplianceEnhancement.wrapped_appliance(self).running_state = RunningState.RUNNING
        return self

    def finish_run(self):
        super().finish_run()
        if self.is_loaded:
            self.needs_unloading = True
        return self

    def to_dict(self):
        return super().to_dict() | {"is_loaded": self.is_loaded, "needs_unloading": self.needs_unloading,
                                    "is_loadable": True}
