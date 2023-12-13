import unittest
from datetime import datetime
from random import Random

from _datetime import timedelta

from iot.infrastructure.room import Room, from_dict
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

    def test_to_dict_contains_all_information(self):
        name = 'Hallway 42'
        temperature = 42.1337
        humidity = 69.12
        last_updated_at = datetime.now() - timedelta(minutes=2)
        last_seen_at = datetime.now() - timedelta(minutes=4)
        # when
        room = Room(name, Temperature(temperature), humidity, last_updated_at, last_seen_at)
        # then
        self.assertEqual(room.to_dict(), {"name": name, "temperature": {"value": temperature, "unit": "degree_celsius"},
                                          "humidity": humidity, "last_updated_at": last_updated_at.isoformat(),
                                          "last_seen_at": last_seen_at.isoformat()})

    def test_contains_all_info_when_creating_from_dict(self):
        name = 'Hallway 42'
        temperature = Temperature(42.1337)
        humidity = 77.12
        last_updated_at = datetime.now() - timedelta(minutes=2)
        last_seen_at = datetime.now() - timedelta(minutes=4)
        # when
        reconstructed_room = from_dict(Room(name, temperature, humidity, last_updated_at, last_seen_at).to_dict())
        # then
        self.assertEqual(name, reconstructed_room.name)
        self.assertEqual(temperature, reconstructed_room.temperature)
        self.assertEqual(humidity, reconstructed_room.humidity)
        self.assertEqual(last_updated_at, reconstructed_room.last_updated_at)
        self.assertEqual(last_seen_at, reconstructed_room.last_seen_at)


if __name__ == '__main__':
    unittest.main()
