import unittest
from unittest.mock import patch, Mock

import paho.mqtt.client

from iot.core.configuration import MqttConfiguration
from iot.mqtt.mqtt_client import MqttClient

patcher = patch('iot.mqtt.mqtt_client.paho_mqtt', autospec=True)
paho_mqtt = patcher.start()
paho_mqtt_client_mock: Mock | paho.mqtt.client.Client = Mock()
paho_mqtt.Client = Mock(return_value=paho_mqtt_client_mock)


class MqttClientTest(unittest.TestCase):
    @patch('iot.core.configuration.MqttConfiguration')
    def setUp(self, mqtt_config_mock):
        self.mqtt_config_mock: Mock | MqttConfiguration = mqtt_config_mock
        paho_mqtt_client_mock.reset_mock()

    def test_mqtt_client_is_started(self):
        # given
        mqtt_client = MqttClient(self.mqtt_config_mock)
        paho_mqtt_client_mock.loop_forever = Mock()
        # when
        mqtt_client.start()
        # then
        paho_mqtt_client_mock.loop_forever.assert_called()

    def test_forwards_sub_to_mqtt_client_when_subscribing(self):
        # given
        mqtt_client = MqttClient(self.mqtt_config_mock)
        paho_mqtt_client_mock.subscribe = Mock()
        topic = "my/important/topic"
        # when
        mqtt_client.subscribe(topic, lambda: "callback")
        # then
        paho_mqtt_client_mock.subscribe.assert_called()

    def test_forwards_sub_on_connect_when_subscribed(self):
        # given
        mqtt_client = MqttClient(self.mqtt_config_mock)
        topic = "my/important/topic"
        mqtt_client.subscribe(topic, lambda: "callback")
        paho_mqtt_client_mock.subscribe = Mock()
        # when
        mqtt_client.on_connect(paho_mqtt_client_mock, None, None, rc=0)
        # then
        paho_mqtt_client_mock.subscribe.assert_called()

    def test_callback_invocation_when_message_matches(self):
        # given
        mqtt_client = MqttClient(self.mqtt_config_mock)
        topic = "my/important/topic"
        msg_mock = Mock(topic=topic, payload="important message")
        callback_mock = Mock()
        # when
        mqtt_client.subscribe(topic, callback_mock)
        mqtt_client.on_message(paho_mqtt_client_mock, None, msg=msg_mock)
        # then
        callback_mock.assert_called_once_with(msg_mock)

    def test_forwards_msg_when_publishing(self):
        # given
        mqtt_client = MqttClient(self.mqtt_config_mock)
        paho_mqtt_client_mock.publish = Mock()
        msg_mock = Mock()
        topic = 'my/important/topic'
        # when
        mqtt_client.publish(topic, msg=msg_mock)
        # then
        paho_mqtt_client_mock.publish.assert_called_once_with(topic, payload=msg_mock)


if __name__ == '__main__':
    unittest.main()
