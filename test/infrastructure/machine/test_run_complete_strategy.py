import random
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from iot.core.storage import Storage
from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.machine.run_complete_strategy import SimpleHistoryRunCompleteStrategy


class TestSimpleHistoryRunCompleteStrategy(unittest.TestCase):
    def setUp(self):
        self.storage_mock: Mock | Storage = Mock()
        self.threshold = 30
        self.duration_to_be_blow_threshold = 300
        self.strategy = SimpleHistoryRunCompleteStrategy(self.storage_mock, self.duration_to_be_blow_threshold,
                                                         self.threshold)

    def test_run_completed_when_history_is_empty(self):
        # given
        self.storage_mock.get_power_consumptions_for_last_seconds = Mock(return_value=[])
        # when
        self.assertTrue(self.strategy.is_run_completed(Mock()))

    def test_run_not_completed_when_history_contains_consumption_above_threshold(self):
        below_threshold_count = 6
        measurements_one_above_threshold = [self.generate_measurement(is_below_threshold=True) for _ in
                                            range(below_threshold_count)]
        measurements_one_above_threshold.insert(random.randint(0, below_threshold_count),
                                                self.generate_measurement(False))
        # given
        self.storage_mock.get_power_consumptions_for_last_seconds = Mock(return_value=measurements_one_above_threshold)
        # when
        self.assertFalse(self.strategy.is_run_completed(Mock()))

    def test_run_completed_when_history_contains_only_below_threshold(self):
        # given
        measurements_below_threshold = [self.generate_measurement(is_below_threshold=True) for _ in range(6)]
        self.storage_mock.get_power_consumptions_for_last_seconds = Mock(return_value=measurements_below_threshold)
        # when
        self.assertTrue(self.strategy.is_run_completed(Mock()))

    def generate_measurement(self, is_below_threshold=True) -> ConsumptionMeasurement:
        time = datetime.now() - timedelta(seconds=random.randint(0, self.duration_to_be_blow_threshold - 1))
        return ConsumptionMeasurement(time,
                                      _below_threshold(self.threshold) if is_below_threshold else _above_threshold(
                                          self.threshold))


def _below_threshold(threshold) -> float: return random.random() * (threshold - .01)


def _above_threshold(threshold) -> float: return threshold + .01 + random.random() * 2000


if __name__ == '__main__':
    unittest.main()
