import unittest

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.units import Temperature


class StorageTest(unittest.TestCase):
    def test_loading_consumption(self):
        db = TimeSeriesStorage()
        # when
        db.append_power_consumption(14.12, "thing01")
        # then
        self.assertTrue(db.get_power_consumptions_for_last_seconds(60, "thing01"))
        self.assertFalse(db.get_power_consumptions_for_last_seconds(60, "thing02"))

    def test_loading_climate(self):
        db = TimeSeriesStorage()
        # when
        db.append_room_climate(Temperature(19.12), 14.12, "thing01")
        # then
        self.assertTrue(db.get_room_climate_for_last_seconds(60, "thing01"))
        self.assertFalse(db.get_room_climate_for_last_seconds(60, "thing02"))


if __name__ == '__main__':
    unittest.main()
