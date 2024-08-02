import logging
from abc import ABCMeta, abstractmethod

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.appliance.appliance import BasicAppliance, RunningState
from iot.infrastructure.appliance.power_state_decorator import PowerState


class RunCompleteStrategy(metaclass=ABCMeta):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__qualname__)

    @abstractmethod
    def is_run_completed(self, appliance):
        pass

    @abstractmethod
    def to_dict(self):
        pass


class SimpleHistoryRunCompleteStrategy(RunCompleteStrategy):
    def __init__(self, time_series_storage: TimeSeriesStorage, duration_to_be_below_threshold: int,
                 power_consumption_threshold: int):
        super().__init__()
        self.time_series_storage = time_series_storage
        self.duration_to_be_below_threshold = duration_to_be_below_threshold
        self.power_consumption_threshold = power_consumption_threshold

    def is_run_completed(self, appliance: BasicAppliance):
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


class FinishedWhenChargingStrategy(RunCompleteStrategy):
    def __init__(self):
        super().__init__()

    def is_run_completed(self, appliance: BasicAppliance):
        try:
            return appliance.running_state == RunningState.LOADING
        except AttributeError:
            raise DetectingFinishedRunFailed("Failed to access running state of appliance %s" % appliance.name)

    def to_dict(self):
        return {
            'name': 'finished_when_loading_strategy'
        }


class DetectingFinishedRunFailed(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
