import unittest
from unittest.mock import Mock

from iot.core.configuration import IotThingConfig, ThresholdsConfig, RangeConfig
from iot.core.storage import Storage
from iot.infrastructure.machine.machine_service import DatabaseException
from iot.infrastructure.room_service import RoomService
from iot.infrastructure.units import Temperature, TemperatureUnit


class InitTest(unittest.TestCase):
    def setUp(self):
        self.storage_mock: Mock | Storage = Mock()
        self.storage_mock.load_thing = Mock(return_value={'name': 'room'})

    def test_loads_from_storage(self):
        # when
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room'))
        # then
        self.storage_mock.load_thing.assert_called_with("Dining room")

    def test_creates_temperature_thresholds(self):
        # given
        temperature_thresholds_config = ThresholdsConfig(RangeConfig(20, 22), 16, 28)
        # when
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room',
                                                                     temperature_thresholds=temperature_thresholds_config))
        # then
        self.assertEqual(20, room_service.room.temperature_thresholds.optimal.lower_value)
        self.assertEqual(22, room_service.room.temperature_thresholds.optimal.upper_value)
        self.assertEqual(16, room_service.room.temperature_thresholds.frostiness_threshold)
        self.assertEqual(28, room_service.room.temperature_thresholds.heat_threshold)

    def test_creates_humidity_thresholds(self):
        # given
        humidity_thresholds_config = ThresholdsConfig(RangeConfig(70, 80), 50, 90)
        # when
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room',
                                                                     humidity_thresholds=humidity_thresholds_config))
        # then
        self.assertEqual(70, room_service.room.humidity_thresholds.optimal.lower_value)
        self.assertEqual(80, room_service.room.humidity_thresholds.optimal.upper_value)
        self.assertEqual(50, room_service.room.humidity_thresholds.drought_threshold)
        self.assertEqual(90, room_service.room.humidity_thresholds.wetness_threshold)


class RoomServiceTest(unittest.TestCase):
    def setUp(self):
        self.storage_mock: Mock | Storage = Mock()
        self.storage_mock.load_thing = Mock(return_value={'name': 'room'})

    def test_saves_updated_temperature_when_updating_temperature(self):
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room'))
        new_temperature = Temperature(21.41, TemperatureUnit.DEGREE_CELSIUS)
        self.storage_mock.update_thing = Mock()
        room_service.room.update_temperature = Mock()
        # when
        room_service.update_temperature(new_temperature)
        # then
        room_service.room.update_temperature.assert_called_with(new_temperature)
        self.storage_mock.update_thing.assert_called_with(room_service.room)

    def test_raises_db_exception_when_storage_fails_while_updating(self):
        room_service = RoomService(self.storage_mock, IotThingConfig(name='Dining room', thing_type='room'))
        room_service.room.update_temperature = Mock(side_effect=[ValueError])
        self.assertRaises(DatabaseException, room_service.update_temperature, Temperature(20))


if __name__ == '__main__':
    unittest.main()
