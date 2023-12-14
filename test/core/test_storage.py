import unittest
from datetime import datetime
from pathlib import Path

from iot.core.storage import Storage
from iot.infrastructure.room import from_dict

DIR = Path(__file__).parent


class StorageTest(unittest.TestCase):
    def test_updating(self):
        db = Storage(Path(DIR / "test.json"), ['thing01'])
        room = from_dict(db.load_thing("thing01"))
        room.humidity = 15.1
        room.last_updated_at = datetime.now()
        # when
        db.update_thing(room)
        # then
        db_obj = db.load_thing("thing01")
        self.assertEqual(room.humidity, db_obj['humidity'])
        self.assertEqual(room.last_updated_at.isoformat(), db_obj['last_updated_at'])

    def test_loading_consumption(self):
        db = Storage(Path(DIR / "test.json"), ['thing01', 'thing02'])
        # when
        db.append_power_consumption(14.12, "thing01")
        # then
        self.assertTrue(db.get_power_consumptions_for_last_seconds(60, "thing01"))
        self.assertFalse(db.get_power_consumptions_for_last_seconds(60, "thing02"))


if __name__ == '__main__':
    unittest.main()
