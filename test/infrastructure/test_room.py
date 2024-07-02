import unittest
from _datetime import timedelta
from datetime import datetime
from random import Random

from iot.infrastructure.room import Room, from_dict
from iot.infrastructure.thing import OnlineStatus
from iot.infrastructure.units import TemperatureUnit, Temperature, TemperatureThresholds, Range, HumidityThresholds, \
    TemperatureRating, HumidityRating


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

    def test_humidity(self):
        humidity = 66.21
        self.assertEqual(Room(name="room_name", humidity=humidity).humidity, humidity)

    def test_temperature_thresholds(self):
        temperature_thresholds = TemperatureThresholds(Range(20, 23), 15, 30)
        self.assertEqual(Room(name="room_name", temperature_thresholds=temperature_thresholds).temperature_thresholds,
                         temperature_thresholds)

    def test_humidity_thresholds(self):
        humidity_thresholds = HumidityThresholds(Range(60, 70), 45, 85)
        self.assertEqual(Room(name="room_name", humidity_thresholds=humidity_thresholds).humidity_thresholds,
                         humidity_thresholds)


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.room = Room(f"Toilette {Random().randint(0, 99)}", Temperature(Random().randint(-4, 28)),
                         last_updated_at=datetime.now() - timedelta(minutes=4),
                         last_seen_at=datetime.now() - timedelta(minutes=10))

    def test_update_temperature(self):
        self.room.temperature = Temperature(12, TemperatureUnit.DEGREE_CELSIUS)
        new_temperature = Temperature(22.34, TemperatureUnit.DEGREE_CELSIUS)
        # when
        room = self.room.update_temperature(new_temperature)
        # then
        self.assertEqual(room.temperature, new_temperature)
        self.assertAlmostEqual(room.last_updated_at, datetime.now(), delta=timedelta(seconds=1))
        self.assertAlmostEqual(room.last_seen_at, datetime.now(), delta=timedelta(seconds=1))

    def test_rate_temperature(self):
        temperature_thresholds = TemperatureThresholds(Range(20, 23), 15, 30)
        self.assertEqual(
            Room("r1", temperature=Temperature(10), temperature_thresholds=temperature_thresholds).rate_temperature(),
            TemperatureRating.CRITICAL_COLD)
        self.assertEqual(
            Room("r2", temperature=Temperature(17), temperature_thresholds=temperature_thresholds).rate_temperature(),
            TemperatureRating.COLD)
        self.assertEqual(
            Room("r3", temperature=Temperature(22), temperature_thresholds=temperature_thresholds).rate_temperature(),
            TemperatureRating.OPTIMAL)
        self.assertEqual(
            Room("r4", temperature=Temperature(25), temperature_thresholds=temperature_thresholds).rate_temperature(),
            TemperatureRating.HOT)
        self.assertEqual(
            Room("r5", temperature=Temperature(31), temperature_thresholds=temperature_thresholds).rate_temperature(),
            TemperatureRating.CRITICAL_HOT)

    def test_update_humidity(self):
        self.room.humidity = 88.2
        new_humidity = 66.42
        # when
        room = self.room.update_humidity(new_humidity)
        # then
        self.assertEqual(room.humidity, new_humidity)
        self.assertAlmostEqual(room.last_updated_at, datetime.now(), delta=timedelta(seconds=1))
        self.assertAlmostEqual(room.last_seen_at, datetime.now(), delta=timedelta(seconds=1))

    def test_rate_humidity(self):
        humidity_thresholds = HumidityThresholds(Range(60, 70), 45, 85)
        self.assertEqual(Room("r1", humidity=40, humidity_thresholds=humidity_thresholds).rate_humidity(),
                         HumidityRating.CRITICAL_DRY)
        self.assertEqual(Room("r2", humidity=50, humidity_thresholds=humidity_thresholds).rate_humidity(),
                         HumidityRating.DRY)
        self.assertEqual(Room("r3", humidity=60, humidity_thresholds=humidity_thresholds).rate_humidity(),
                         HumidityRating.OPTIMAL)
        self.assertEqual(Room("r4", humidity=75, humidity_thresholds=humidity_thresholds).rate_humidity(),
                         HumidityRating.WET)
        self.assertEqual(Room("r5", humidity=90, humidity_thresholds=humidity_thresholds).rate_humidity(),
                         HumidityRating.CRITICAL_WET)

    def test_to_dict_contains_all_information(self):
        name = 'Hallway 42'
        temperature = 42.1337
        humidity = 69.12
        temperature_thresholds = TemperatureThresholds(Range(20, 23), 15, 30)
        humidity_thresholds = HumidityThresholds(Range(60, 70), 45, 85)
        last_updated_at = datetime.now() - timedelta(minutes=2)
        last_seen_at = datetime.now() - timedelta(minutes=4)
        # when
        room = Room(name, Temperature(temperature), humidity, temperature_thresholds, humidity_thresholds,
                    last_updated_at, last_seen_at)
        # then
        self.assertEqual(room.to_dict(),
                         {"name": name, "type": "room", "temperature": {"value": temperature, "unit": "degree_celsius"},
                          "humidity": humidity, 'temperature_thresholds': {'frostiness_threshold': 15,
                                                                           'heat_threshold': 30,
                                                                           'optimal_lower': 20,
                                                                           'optimal_upper': 23},
                          "temperature_rating": TemperatureRating.CRITICAL_HOT,
                          'humidity_thresholds': {'drought_threshold': 45,
                                                  'optimal_lower': 60,
                                                  'optimal_upper': 70,
                                                  'wetness_threshold': 85},
                          "humidity_rating": HumidityRating.OPTIMAL,
                          "online_status": OnlineStatus.ONLINE,
                          "last_updated_at": last_updated_at.isoformat(),
                          "last_seen_at": last_seen_at.isoformat()})

    def test_contains_all_info_when_creating_from_dict(self):
        name = 'Hallway 42'
        temperature = Temperature(42.1337)
        humidity = 77.12
        temperature_thresholds = TemperatureThresholds(Range(20, 23), 15, 30)
        humidity_thresholds = HumidityThresholds(Range(60, 70), 45, 85)
        last_updated_at = datetime.now() - timedelta(minutes=2)
        last_seen_at = datetime.now() - timedelta(minutes=4)
        # when
        reconstructed_room = from_dict(
            Room(name, temperature, humidity, temperature_thresholds, humidity_thresholds,
                 last_updated_at, last_seen_at).to_dict())
        # then
        self.assertEqual(name, reconstructed_room.name)
        self.assertEqual(temperature, reconstructed_room.temperature)
        self.assertEqual(humidity, reconstructed_room.humidity)
        self.assertEqual(temperature_thresholds, reconstructed_room.temperature_thresholds)
        self.assertEqual(humidity_thresholds, reconstructed_room.humidity_thresholds)
        self.assertEqual(last_updated_at, reconstructed_room.last_updated_at)
        self.assertEqual(last_seen_at, reconstructed_room.last_seen_at)


if __name__ == '__main__':
    unittest.main()
