import logging

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.machine.iot_machine import IotMachine
from iot.infrastructure.machine.power_state_decorator import PowerState


class SimpleHistoryRunCompleteStrategy:
    def __init__(self, time_series_storage: TimeSeriesStorage, duration_to_be_below_threshold=300,
                 power_consumption_threshold=10):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.time_series_storage = time_series_storage
        self.duration_to_be_below_threshold = duration_to_be_below_threshold
        self.power_consumption_threshold = power_consumption_threshold

    def is_run_completed(self, thing: IotMachine):
        if thing.power_state is PowerState.RUNNING:
            return False
        measures = self.time_series_storage.get_power_consumptions_for_last_seconds(self.duration_to_be_below_threshold,
                                                                                    thing.name)
        if any(measure.consumption > self.power_consumption_threshold for measure in measures):
            self.logger.debug("Thing '%s' is still running based on history: %s", thing.name, measures)
            return False
        self.logger.debug("Run of thing '%s' is complete based on history: %s", thing.name, measures)
        return True
