import time
import unittest
from unittest.mock import patch, Mock, ANY, call

from iot.core.configuration import PlannedNotification, Destinations
from iot.mqtt.MqttClient import MqttClient


class MyTestCase(unittest.TestCase):
    @patch('iot.core.configuration.Destinations')
    @patch('iot.core.configuration.Sources')
    @patch('iot.core.configuration.MqttConfiguration')
    @patch('iot.machine.MachineService.MachineService')
    def setUp(self, machine_service_mock, mqtt_config_mock, sources_mock, destinations_mock):
        self.machine_service_mock = machine_service_mock
        self.mqtt_config_mock = mqtt_config_mock
        self.sources_mock = sources_mock
        self.destinations_mock = destinations_mock

        patcher = patch('iot.mqtt.MqttClient.paho_mqtt', autospec=True)
        self.mock_client = patcher.start()

    def test_notifies_every_second_when_specified_by_cron(self):
        # given
        notify_every_second = "* * * * * *"
        destinations = Destinations(list([PlannedNotification("some/topic", notify_every_second)]))
        self.mqtt_client = MqttClient(self.machine_service_mock, self.mqtt_config_mock, self.sources_mock, destinations)
        self.mqtt_client.mqtt_client.publish = Mock()
        # when
        self.mqtt_client.start()
        time.sleep(2)
        # then
        self.mqtt_client.mqtt_client.publish.assert_has_calls([call("some/topic", ANY), call("some/topic", ANY)])


if __name__ == '__main__':
    unittest.main()
