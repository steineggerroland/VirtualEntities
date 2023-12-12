import unittest
from datetime import datetime
from random import Random

from _datetime import timedelta

from iot.infrastructure.room import Room
from iot.infrastructure.units import TemperatureUnit, Temperature


class InitTest(unittest.TestCase):
    def test_name(self):
        room_name = "Bathroom"
        self.assertEqual(Room(name=room_name).name, room_name)

    def test_last_updated_at(self):
        last_updated_at = datetime.now()
        self.assertEqual(Room(name="room_name", last_updated_at=last_updated_at).last_updated_at, last_updated_at)

    def test_last_seen_at(self):
        last_seen_at = datetime.now()
        self.assertEqual(Room(name="room_name", last_seen_at=last_seen_at).last_seen_at, last_seen_at)

    def test_temperature(self):
        temperature = Temperature(value=14, unit=TemperatureUnit.DEGREE_CELSIUS)
        self.assertEqual(Room(name="room_name", temperature=temperature).temperature, temperature)


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.room = Room(f"Toilette {Random().randint(0, 99)}", Temperature(Random().randint(-4, 28)),
                         last_updated_at=datetime.now() - timedelta(minutes=4),
                         last_seen_at=datetime.now() - timedelta(minutes=10))

    def test_update_temperature(self):
        self.room.temperature = Temperature(12, TemperatureUnit.DEGREE_CELSIUS)
        new_temperature = Temperature(22.34, TemperatureUnit.DEGREE_CELSIUS)
        # when
        self.room.update_temperature(new_temperature)
        # then
        self.assertEqual(self.room.temperature, new_temperature)
        self.assertAlmostEqual(self.room.last_updated_at, datetime.now(), delta=timedelta(seconds=1))
        self.assertAlmostEqual(self.room.last_seen_at, datetime.now(), delta=timedelta(seconds=1))


if __name__ == '__main__':
    unittest.main()
