import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, ANY, patch, call

from dateutil.tz import tzlocal
from waiting import wait

from iot.core.configuration import VirtualEntityConfig, Sources, MqttMeasureSource, Destinations, PlannedNotification, \
    Measure
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.room import Room
from iot.infrastructure.room_service import RoomService
from iot.infrastructure.units import Temperature, HumidityThresholds, Range, TemperatureThresholds
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_room_mediator import MqttRoomMediator

DIR = Path(__file__).parent


def _set_up_croniter():
    # cron is replaced to announce two immediate responses and one in a week
    patcher = patch('iot.mqtt.mqtt_mediator.croniter')
    croniter_mock = patcher.start()
    croniter = Mock()
    croniter.get_next = Mock(
        side_effect=[datetime.now(tzlocal()), datetime.now(tzlocal()), datetime.now(tzlocal()) + timedelta(weeks=1)])
    croniter_mock.return_value = croniter


class TemperatureTest(unittest.TestCase):
    def setUp(self):
        self.room_service_mock: RoomService = Mock()
        self.room_service_mock.room.to_dict = Mock(return_value={})
        self.mqtt_client_mock: MqttClient = Mock()

    def test_subscribes_for_temp_when_init(self):
        entity_config = VirtualEntityConfig("Kitchen", "room",
                                            sources=Sources(
                                                [MqttMeasureSource(mqtt_topic="some/topic",
                                                                   measures=[
                                                                       Measure(source_type='temperature', path="$")])]))
        # when
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, entity_config)
        # then
        self.mqtt_client_mock.subscribe.assert_called_with(ANY, "some/topic", ANY)

    def test_forwards_to_mediator_when_updating_temperature_with_jsonpath(self):
        entity_config = VirtualEntityConfig("Kitchen", "room",
                                            sources=Sources([MqttMeasureSource(mqtt_topic="some/topic", measures=[
                                                Measure(source_type='temperature', path="$.temperature")])]))
        mediator = MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, entity_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][2]
        self.room_service_mock.update_temperature = Mock()
        temperature = Temperature(23.12)
        msg = bytes(
            '{"battery":100,"humidity":71.65,"linkquality":216,"temperature":%s,"voltage":3000}' % temperature.value,
            "utf-8")
        # when
        mqtt_callback(Mock(mqtt_topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_called_once()
        self.assertEqual(temperature, self.room_service_mock.update_temperature.call_args[0][0])

    def test_forwards_to_mediator_when_updating_temperature_without_jsonpath(self):
        entity_config = VirtualEntityConfig("Kitchen", "room",
                                            sources=Sources([MqttMeasureSource(mqtt_topic="some/topic", measures=[
                                                Measure(source_type='temperature')])]))
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, entity_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][2]
        self.room_service_mock.update_temperature = Mock()
        temperature = Temperature(23.12)
        msg = b"23.12"
        # when
        mqtt_callback(Mock(mqtt_topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_called_once()
        self.assertEqual(temperature, self.room_service_mock.update_temperature.call_args[0][0])

    def test_no_error_when_json_path_not_found(self):
        unsupported_json_path = "$.unknownPath"
        entity_config = VirtualEntityConfig("Kitchen", "room",
                                            sources=Sources(
                                                [MqttMeasureSource(mqtt_topic="some/topic", measures=[
                                                    Measure(source_type='temperature',
                                                            path=unsupported_json_path)])]))
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, entity_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][2]
        self.room_service_mock.update_temperature = Mock()
        msg = b'{"battery":100,"humidity":71.65,"linkquality":216,"temperature":23.12,"voltage":3000}'
        # when
        mqtt_callback(Mock(mqtt_topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_not_called()

    def test_no_error_when_not_json_with_jsonpath(self):
        unsupported_json_path = "$.unknownPath"
        entity_config = VirtualEntityConfig("Kitchen", "room",
                                            sources=Sources(
                                                [MqttMeasureSource(mqtt_topic="some/topic", measures=[
                                                    Measure(source_type='temperature',
                                                            path=unsupported_json_path)])]))
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, entity_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][2]
        self.room_service_mock.update_temperature = Mock()
        msg = b"21.3"
        # when
        mqtt_callback(Mock(mqtt_topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_not_called()

    def test_publishing_updates_when_specified(self):
        # given
        destinations = Destinations([PlannedNotification("some/topic", "* * * * * *")])
        mqtt_room_mediator = MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock,
                                              entity_config=VirtualEntityConfig("Kitchen", "room",
                                                                                destinations=destinations))
        _set_up_croniter()
        # when
        mqtt_room_mediator.start()
        # then
        wait(lambda: sum(publish_args == call("some/topic", ANY) for publish_args in
                         self.mqtt_client_mock.publish.call_args_list) >= 2, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")

    def test_update_format_when_publishing(self):
        # given
        destinations = Destinations([PlannedNotification("some/topic", "* * * * * *")])
        mqtt_room_mediator = MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock,
                                              entity_config=VirtualEntityConfig("Kitchen", "room",
                                                                                destinations=destinations))
        self._set_up_room_matching_json()
        _set_up_croniter()
        # when
        mqtt_room_mediator.start()
        # then
        with Path.open(DIR / "room-update.json") as file:
            expected_json = json.loads(file.read())
            # enums have to be converted
            expected_json['last_seen_at'] = datetime.fromisoformat(expected_json['last_seen_at']).astimezone(
                tzlocal()).isoformat()
            expected_json['last_updated_at'] = datetime.fromisoformat(expected_json['last_updated_at']).astimezone(
                tzlocal()).isoformat()
            wait(lambda: sum(publish_args == call(ANY, ANY) for publish_args in
                             self.mqtt_client_mock.publish.call_args_list) >= 1, timeout_seconds=1,
                 waiting_for="mqtt.publish called several times")
            self.assertDictEqual(expected_json, self.mqtt_client_mock.publish.call_args_list[0].args[1])

    def _set_up_room_matching_json(self):
        self.room_service_mock.get_room = lambda: Room("kitchen", Temperature(13.37), 42.42,
                                                       TemperatureThresholds(Range(18, 22), 16, 30),
                                                       HumidityThresholds(Range(50, 60), 40, 80),
                                                       datetime.fromisoformat("2024-01-02T03:04:05.678910").astimezone(tzlocal()),
                                                       datetime.fromisoformat("2024-01-01T01:01:01.111111").astimezone(tzlocal()))

    def test_handles_database_exceptions_without_breaking(self):
        mqtt_mediator = MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, VirtualEntityConfig())

        self.room_service_mock.update_temperature = Mock(side_effect=DatabaseException)
        mqtt_mediator.temperature_update(Mock(mqtt_topic="temperature/topic", payload='23.1'))

        self.room_service_mock.update_humidity = Mock(side_effect=DatabaseException)
        mqtt_mediator.humidity_update(Mock(mqtt_topic="humidity/topic", payload='45'))

        self.room_service_mock.update_room_climate = Mock(side_effect=DatabaseException)
        mqtt_mediator.update_room_climate(
            Mock(mqtt_topic="climat/topic", payload='{"temperature": 12.1, "humidity": 44}'),
            "$.temperature", "$.humidity")


if __name__ == '__main__':
    unittest.main()
