import unittest
from datetime import datetime
from unittest.mock import patch, Mock, call

from waiting import wait

from iot.core.configuration import PlannedNotification, Destinations
from iot.mqtt.MqttClient import MqttClient


class MyTestCase(unittest.TestCase):
    @patch('iot.core.configuration.Destinations')
    @patch('iot.core.configuration.Sources')
    @patch('iot.core.configuration.MqttConfiguration')
    @patch('iot.machine.MachineService.MachineService')
    def setUp(self, machine_service_mock, mqtt_config_mock, sources_mock, destinations_mock):
        self.machine_service_mock = machine_service_mock
        self.machine_service_mock.thing.to_dict = Mock(return_value={})
        self.mqtt_config_mock = mqtt_config_mock
        self.sources_mock = sources_mock
        self.destinations_mock = destinations_mock

        patcher = patch('iot.mqtt.MqttClient.paho_mqtt', autospec=True)
        paho_mqtt = patcher.start()
        self.paho_mqtt_client_mock = Mock()
        paho_mqtt.Client = Mock(return_value=self.paho_mqtt_client_mock)

    def test_notifies_every_second_when_specified_by_cron(self):
        # given
        destinations = Destinations(list([PlannedNotification("some/topic", "* * * * * *")]))
        mqtt_client = MqttClient(self.machine_service_mock, self.mqtt_config_mock, self.sources_mock, destinations)
        # cron is replaced to announce immediate response
        patcher = patch('iot.mqtt.MqttClient.croniter')
        croniter_mock = patcher.start()
        croniter = Mock()
        croniter.get_next = lambda e: datetime.now()
        croniter_mock.return_value = croniter
        # when
        mqtt_client.start()
        # then
        wait(lambda: sum(publish_args == call("some/topic", "{}") for publish_args in
                         self.paho_mqtt_client_mock.publish.call_args_list) > 10, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")


if __name__ == '__main__':
    unittest.main()
