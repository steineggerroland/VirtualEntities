import unittest
from datetime import datetime
from pathlib import Path

from iot.core.storage import Storage
from iot.infrastructure.room import Room

DIR = Path(__file__).parent


class StorageTest(unittest.TestCase):
    def test_updating(self):
        db = Storage(Path(DIR / "test.json"), ['entity01'])
        room = Room("entity01")
        room.humidity = 15.1
        room.last_updated_at = datetime.now()
        # when
        db.update(room)
        # then
        db_obj = db.load_room("entity01")
        self.assertEqual(room.humidity, db_obj.humidity)
        self.assertEqual(room.last_updated_at, db_obj.last_updated_at)


if __name__ == '__main__':
    unittest.main()
