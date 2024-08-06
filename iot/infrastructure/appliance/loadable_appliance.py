from datetime import datetime

from dateutil.tz import tzlocal

from iot.infrastructure.appliance.appliance import RunningState, BasicAppliance
from iot.infrastructure.appliance.appliance_enhancements import ApplianceEnhancement


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
