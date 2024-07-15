import logging

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.appliance.appliance import Appliance
from iot.infrastructure.appliance.power_state_decorator import PowerState


class SimpleHistoryRunCompleteStrategy:
    def __init__(self, time_series_storage: TimeSeriesStorage, duration_to_be_below_threshold: int,
                 power_consumption_threshold: int):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.time_series_storage = time_series_storage
        self.duration_to_be_below_threshold = duration_to_be_below_threshold
        self.power_consumption_threshold = power_consumption_threshold

    def is_run_completed(self, appliance: Appliance):
        if appliance.power_state is PowerState.RUNNING:
            return False
        measures = self.time_series_storage.get_power_consumptions_for_last_seconds(self.duration_to_be_below_threshold,
                                                                                    appliance.name)
        if any(measure.consumption > self.power_consumption_threshold for measure in measures):
            self.logger.debug("Appliance '%s' is still running based on history: %s", appliance.name, measures)
            return False
        self.logger.debug("Run of appliance '%s' is complete based on history: %s", appliance.name, measures)
        return True

    def to_dict(self) -> dict:
        return {
            'name': 'simple_history_run_complete_strategy',
            'duration_to_be_below_threshold': self.duration_to_be_below_threshold,
            'power_consumption_threshold': self.power_consumption_threshold
        }
