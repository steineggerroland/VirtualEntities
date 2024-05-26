import unittest
from unittest.mock import Mock

from iot.core.configuration import IotThingConfig, ThresholdsConfig, RangeConfig
from iot.core.storage import Storage
from iot.infrastructure.machine.machine_service import DatabaseException
from iot.infrastructure.room import Room
from iot.infrastructure.room_service import RoomService
from iot.infrastructure.units import Temperature, TemperatureUnit


class InitTest(unittest.TestCase):
    def setUp(self):
        self.storage_mock: Mock | Storage = Mock()
        self.room_name = "Dining hall"
        self.room = Room(name=self.room_name)
        self.storage_mock.load_room = Mock(return_value=self.room)

    def test_loads_from_storage(self):
        # when
        RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room'))
        # then
        self.storage_mock.load_room.assert_called_with("Dining room")

    def test_creates_temperature_thresholds(self):
        # given
        temperature_thresholds_config = ThresholdsConfig(RangeConfig(20, 22), 16, 28)
        # when
        RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room',
                                                      temperature_thresholds=temperature_thresholds_config))
        # then
        updated_room_arg: Room = self.storage_mock.update_thing.call_args[0][0]
        self.assertEqual(20, updated_room_arg.temperature_thresholds.optimal.lower_value)
        self.assertEqual(22, updated_room_arg.temperature_thresholds.optimal.upper_value)
        self.assertEqual(16, updated_room_arg.temperature_thresholds.frostiness_threshold)
        self.assertEqual(28, updated_room_arg.temperature_thresholds.heat_threshold)

    def test_creates_humidity_thresholds(self):
        # given
        humidity_thresholds_config = ThresholdsConfig(RangeConfig(70, 80), 50, 90)
        # when
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room',
                                                                     humidity_thresholds=humidity_thresholds_config))
        # then
        updated_room_arg: Room = self.storage_mock.update_thing.call_args[0][0]
        self.assertEqual(70, updated_room_arg.humidity_thresholds.optimal.lower_value)
        self.assertEqual(80, updated_room_arg.humidity_thresholds.optimal.upper_value)
        self.assertEqual(50, updated_room_arg.humidity_thresholds.drought_threshold)
        self.assertEqual(90, updated_room_arg.humidity_thresholds.wetness_threshold)


class RoomServiceTest(unittest.TestCase):
    def setUp(self):
        self.storage_mock: Mock | Storage = Mock()
        self.room = Room("Kitchen")
        self.storage_mock.load_room = Mock(return_value=self.room)

    def test_saves_updated_temperature_when_updating_temperature(self):
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room'))
        new_temperature = Temperature(21.41, TemperatureUnit.DEGREE_CELSIUS)
        self.storage_mock.update_thing = Mock()
        self.room.update_temperature = Mock()
        # when
        room_service.update_temperature(new_temperature)
        # then
        self.room.update_temperature.assert_called_with(new_temperature)
        self.storage_mock.update_thing.assert_called()

    def test_raises_db_exception_when_storage_fails_while_updating(self):
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room'))
        self.room.update_temperature = Mock(side_effect=[ValueError])
        self.assertRaises(DatabaseException, room_service.update_temperature, Temperature(20))


if __name__ == '__main__':
    unittest.main()
