import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, ANY, patch, call

from waiting import wait

from iot.core.configuration import IotThingConfig, Sources, Source, Destinations, PlannedNotification
from iot.infrastructure.room_service import RoomService
from iot.infrastructure.units import Temperature
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_room_mediator import MqttRoomMediator


class TemperatureTest(unittest.TestCase):
    def setUp(self):
        self.room_service_mock: RoomService = Mock()
        self.room_service_mock.room.to_dict = Mock(return_value={})
        self.mqtt_client_mock: MqttClient = Mock()

    def test_subscribes_for_temp_when_init(self):
        thing_config = IotThingConfig("Kitchen", "room",
                                      sources=Sources(
                                          [Source(topic="some/topic", source_type='temperature', path="$")]))
        self.mqtt_client_mock.subscribe = Mock()
        # when
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, thing_config)
        # then
        self.mqtt_client_mock.subscribe.assert_called_with("some/topic", ANY)

    def test_forwards_to_mediator_when_updating_temperature_with_jsonpath(self):
        thing_config = IotThingConfig("Kitchen", "room",
                                      sources=Sources([Source(topic="some/topic", source_type='temperature',
                                                              path="$.temperature")]))
        self.mqtt_client_mock.subscribe = Mock()
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, thing_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][1]
        self.room_service_mock.update_temperature = Mock()
        temperature = Temperature(23.12)
        msg = bytes(
            '{"battery":100,"humidity":71.65,"linkquality":216,"temperature":%s,"voltage":3000}' % temperature.value,
            "utf-8")
        # when
        mqtt_callback(Mock(topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_called_once()
        self.assertEqual(temperature, self.room_service_mock.update_temperature.call_args[0][0])

    def test_forwards_to_mediator_when_updating_temperature_without_jsonpath(self):
        thing_config = IotThingConfig("Kitchen", "room",
                                      sources=Sources([Source(topic="some/topic", source_type='temperature')]))
        self.mqtt_client_mock.subscribe = Mock()
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, thing_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][1]
        self.room_service_mock.update_temperature = Mock()
        temperature = Temperature(23.12)
        msg = b"23.12"
        # when
        mqtt_callback(Mock(topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_called_once()
        self.assertEqual(temperature, self.room_service_mock.update_temperature.call_args[0][0])

    def test_no_error_when_json_path_not_found(self):
        unsupported_json_path = "$.unknownPath"
        thing_config = IotThingConfig("Kitchen", "room",
                                      sources=Sources(
                                          [Source(topic="some/topic", source_type='temperature',
                                                  path=unsupported_json_path)]))
        self.mqtt_client_mock.subscribe = Mock()
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, thing_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][1]
        self.room_service_mock.update_temperature = Mock()
        msg = b'{"battery":100,"humidity":71.65,"linkquality":216,"temperature":23.12,"voltage":3000}'
        # when
        mqtt_callback(Mock(topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_not_called()

    def test_no_error_when_not_json_with_jsonpath(self):
        unsupported_json_path = "$.unknownPath"
        thing_config = IotThingConfig("Kitchen", "room",
                                      sources=Sources(
                                          [Source(topic="some/topic", source_type='temperature',
                                                  path=unsupported_json_path)]))
        self.mqtt_client_mock.subscribe = Mock()
        MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock, thing_config)
        mqtt_callback = self.mqtt_client_mock.subscribe.call_args[0][1]
        self.room_service_mock.update_temperature = Mock()
        msg = b"21.3"
        # when
        mqtt_callback(Mock(topic="some/topic", payload=msg))
        # then
        self.room_service_mock.update_temperature.assert_not_called()

    def test_publishing_updates_when_specified(self):
        # given
        destinations = Destinations([PlannedNotification("some/topic", "* * * * * *")])
        mqtt_room_mediator = MqttRoomMediator(self.mqtt_client_mock, self.room_service_mock,
                                              thing_config=IotThingConfig("Kitchen", "room", destinations=destinations))
        self.mqtt_client_mock.publish = Mock()
        # cron is replaced to announce two immediate responses and one in a week
        patcher = patch('iot.mqtt.mqtt_mediator.croniter')
        croniter_mock = patcher.start()
        croniter = Mock()
        croniter.get_next = Mock(side_effect=[datetime.now(), datetime.now(), datetime.now() + timedelta(weeks=1)])
        croniter_mock.return_value = croniter
        # when
        mqtt_room_mediator.start()
        # then
        wait(lambda: sum(publish_args == call("some/topic", ANY) for publish_args in
                         self.mqtt_client_mock.publish.call_args_list) >= 2, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")


if __name__ == '__main__':
    unittest.main()
