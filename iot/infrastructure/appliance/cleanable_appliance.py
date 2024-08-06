from datetime import datetime

from dateutil.tz import tzlocal

from iot.infrastructure.appliance.appliance import RunningState, BasicAppliance
from iot.infrastructure.appliance.appliance_enhancements import ApplianceEnhancement


class CleanableAppliance(ApplianceEnhancement):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'clean') and
                callable(subclass.clean) and
                hasattr(subclass, 'notice_dirt') and
                callable(subclass.notice_dirt) and
                hasattr(subclass, 'needs_cleaning') or
                NotImplemented)

    def __init__(self, appliance_to_enhance: BasicAppliance, needs_cleaning=None):
        """
        An appliance that gets dirty while using and needs to be cleaned from time to time.
        By default, the appliance is marked as dirty after each run. Check whether an appliance 'needs_cleaning' and
        'clean()' it or 'notice_dirt()'.

        :param appliance_to_enhance: to enhance with attributes and methods of a cleanable appliance
        :param needs_cleaning: whether the appliance needs to be cleaned or not
        """
        super().__init__(appliance_to_enhance)
        self.needs_cleaning = needs_cleaning if needs_cleaning is not None else False
        self.is_cleanable = True

    def clean(self):
        self.needs_cleaning = False
        ApplianceEnhancement.wrapped_appliance(self).last_updated_at = datetime.now(tzlocal())
        return self

    def notice_dirt(self, needs_cleaning=True):
        self.needs_cleaning = needs_cleaning if not ApplianceEnhancement.wrapped_appliance(
            self).running_state == RunningState.RUNNING else False
        ApplianceEnhancement.wrapped_appliance(self).last_updated_at = datetime.now(tzlocal())
        return self

    def start_run(self):
        super().start_run()
        self.needs_cleaning = False
        return self

    def finish_run(self):
        super().finish_run()
        self.needs_cleaning = True
        return self

    def to_dict(self):
        return super().to_dict() | {"needs_cleaning": self.needs_cleaning, "is_cleanable": True}
