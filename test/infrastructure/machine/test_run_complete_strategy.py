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
        # given
        self.storage_mock.get_power_consumptions_for_last_seconds = Mock(
            return_value=[self.generate_measurement(is_below_threshold=True),
                          self.generate_measurement(is_below_threshold=False),
                          self.generate_measurement(is_below_threshold=True),
                          self.generate_measurement(is_below_threshold=True)])
        # when
        self.assertFalse(self.strategy.is_run_completed(Mock()))

    def test_run_completed_when_history_contains_only_below_threshold(self):
        # given
        self.storage_mock.get_power_consumptions_for_last_seconds = Mock(
            return_value=[self.generate_measurement(is_below_threshold=True),
                          self.generate_measurement(is_below_threshold=True),
                          self.generate_measurement(is_below_threshold=True),
                          self.generate_measurement(is_below_threshold=True)])
        # when
        self.assertTrue(self.strategy.is_run_completed(Mock()))

    def generate_measurement(self, is_below_threshold=True) -> ConsumptionMeasurement:
        time = datetime.now() - timedelta(seconds=random.randint(0, self.duration_to_be_blow_threshold - 1))
        return ConsumptionMeasurement(time, (random.random() * (self.threshold - .01)) if is_below_threshold else (
                self.threshold + .01 + random.random() * 2000))


if __name__ == '__main__':
    unittest.main()
