import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from iot.core.timeseries_storage_in_memory import InMemoryTimeSeriesStorageStrategy
from iot.infrastructure.units import Temperature


class InMemoryStorageTest(unittest.TestCase):
    @patch("iot.core.timeseries_storage_in_memory.datetime")
    def test_storing_consumption(self, datetime_mock):
        db = InMemoryTimeSeriesStorageStrategy()
        now = datetime.now()
        datetime_mock.now.return_value = now
        # when
        db.append_power_consumption(14.12, "thing01")
        # then
        # reset behavior of mock
        datetime_mock.now.return_value = datetime.now()
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        saved_consumption = db.get_power_consumptions_for_last_seconds(60, "thing01").pop()
        self.assertEqual(saved_consumption.consumption, 14.12)
        self.assertEqual(saved_consumption.time, now)

    def test_returns_only_for_thing_consumption(self):
        db = InMemoryTimeSeriesStorageStrategy()
        now = datetime.now()
        # when
        db.append_power_consumption(14.12, "thing01")
        # then
        self.assertFalse(db.get_power_consumptions_for_last_seconds(60, "other thing"))

    @patch("iot.core.timeseries_storage_in_memory.datetime")
    def test_loading_consumption(self, datetime_mock: Mock):
        db = InMemoryTimeSeriesStorageStrategy()
        # when
        datetime_mock.now.return_value = datetime.now() - timedelta(days=1)
        db.append_power_consumption(1, "thing01")
        datetime_mock.now.return_value = datetime.now() - timedelta(hours=1)
        db.append_power_consumption(2, "thing01")
        datetime_mock.now.return_value = datetime.now() - timedelta(minutes=1)
        db.append_power_consumption(3, "thing01")
        datetime_mock.now.return_value = datetime.now()
        db.append_power_consumption(4, "thing01")
        # then
        # reset behavior of mock
        datetime_mock.now.return_value = datetime.now()
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        self.assertEqual(len(db.get_power_consumptions_for_last_seconds(5, "thing01")), 1)
        self.assertEqual(len(db.get_power_consumptions_for_last_seconds(60 + 5, "thing01")), 2)
        self.assertEqual(len(db.get_power_consumptions_for_last_seconds(60 * 60 + 5, "thing01")), 3)

    @patch("iot.core.timeseries_storage_in_memory.datetime")
    def test_just_keeps_ten_consumptions(self, datetime_mock: Mock):
        db = InMemoryTimeSeriesStorageStrategy()
        # when
        datetime_mock.now.return_value = datetime.now()
        for watt in range(20):
            db.append_power_consumption(watt, "thing01")
        # then
        # reset behavior of mock
        datetime_mock.now.return_value = datetime.now()
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        consumptions = db.get_power_consumptions_for_last_seconds(60, "thing01")
        for watt in range(11, 20):
            self.assertIn(watt, list(map(lambda c: c.consumption, consumptions)))

    @patch("iot.core.timeseries_storage_in_memory.datetime")
    def test_storing_climate(self, datetime_mock: Mock):
        db = InMemoryTimeSeriesStorageStrategy()
        now = datetime.now()
        datetime_mock.now.return_value = now
        # when
        db.append_room_climate(Temperature(23.1), 14.12, "thing01")
        # then
        # reset behavior of mock
        datetime_mock.now.return_value = datetime.now()
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        measure = db.get_room_climate_for_last_seconds(60, "thing01").pop()
        self.assertEqual(measure.temperature, 23.1)
        self.assertEqual(measure.humidity, 14.12)
        self.assertEqual(measure.time, now)

    def test_only_returns_for_thing_climate(self):
        db = InMemoryTimeSeriesStorageStrategy()
        # when
        db.append_room_climate(Temperature(23.1), 14.12, "thing01")
        # then
        self.assertFalse(db.get_room_climate_for_last_seconds(60, "other thing"))

    @patch("iot.core.timeseries_storage_in_memory.datetime")
    def test_getting_in_time_range_consumption(self, datetime_mock: Mock):
        db = InMemoryTimeSeriesStorageStrategy()
        # when
        datetime_mock.now.return_value = datetime.now() - timedelta(days=1)
        db.append_room_climate(Temperature(21), 1, "thing01")
        datetime_mock.now.return_value = datetime.now() - timedelta(hours=1)
        db.append_room_climate(Temperature(22), 2, "thing01")
        datetime_mock.now.return_value = datetime.now() - timedelta(minutes=1)
        db.append_room_climate(Temperature(23), 3, "thing01")
        datetime_mock.now.return_value = datetime.now()
        db.append_room_climate(Temperature(24), 4, "thing01")
        # then
        # reset behavior of mock
        datetime_mock.now.return_value = datetime.now()
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        self.assertEqual(len(db.get_room_climate_for_last_seconds(5, "thing01")), 1)
        self.assertEqual(len(db.get_room_climate_for_last_seconds(60 + 5, "thing01")), 2)
        self.assertEqual(len(db.get_room_climate_for_last_seconds(60 * 60 + 5, "thing01")), 3)

    @patch("iot.core.timeseries_storage_in_memory.datetime")
    def test_just_keeps_ten_climates(self, datetime_mock: Mock):
        db = InMemoryTimeSeriesStorageStrategy()
        # when
        datetime_mock.now.return_value = datetime.now()
        for index in range(20):
            db.append_room_climate(Temperature(index), index, "thing01")
        # then
        # reset behavior of mock
        datetime_mock.now.return_value = datetime.now()
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        climates = db.get_room_climate_for_last_seconds(60, "thing01")
        for index in range(11, 20):
            self.assertIn(index, list(map(lambda c: c.humidity, climates)))
            self.assertIn(index, list(map(lambda c: c.temperature, climates)))


if __name__ == '__main__':
    unittest.main()
