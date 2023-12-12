import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, call

from waiting import wait

from iot.core.configuration import PlannedNotification, Destinations, Sources
from iot.infrastructure.machine.machine_service import MachineService
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_machine_mediator import MqttMediator


class MqttMediatorTest(unittest.TestCase):
    @patch('iot.mqtt.mqtt_client')
    @patch('iot.core.configuration.Destinations')
    @patch('iot.core.configuration.Sources')
    @patch('iot.core.configuration.MqttConfiguration')
    @patch('iot.infrastructure.machine.machine_service.MachineService')
    def setUp(self, machine_service_mock, mqtt_config_mock, sources_mock, destinations_mock, mqtt_client_mock):
        self.machine_service_mock: Mock | MachineService = machine_service_mock
        self.machine_service_mock.thing.to_dict = Mock(return_value={})
        self.mqtt_config_mock = mqtt_config_mock
        self.sources_mock: Mock | Sources = sources_mock
        self.destinations_mock: Mock | Destinations = destinations_mock
        self.mqtt_client_mock: Mock | MqttClient = mqtt_client_mock

    def test_updates_when_specified_by_cron(self):
        # given
        destinations = Destinations(list([PlannedNotification("some/topic", "* * * * * *")]))
        mqtt_mediator = MqttMediator(self.machine_service_mock, self.mqtt_config_mock, self.sources_mock, destinations,
                                     self.mqtt_client_mock)
        # cron is replaced to announce two immediate responses and one in a week
        patcher = patch('iot.mqtt.mqtt_mediator.croniter')
        croniter_mock = patcher.start()
        croniter = Mock()
        croniter.get_next = Mock(side_effect=[datetime.now(), datetime.now(), datetime.now() + timedelta(weeks=1)])
        croniter_mock.return_value = croniter
        # when
        mqtt_mediator.start()
        # then
        wait(lambda: sum(publish_args == call("some/topic", "{}") for publish_args in
                         self.mqtt_client_mock.publish.call_args_list) >= 2, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")

    def test_subscribes_for_consumption_on_start(self):
        # given
        consumption_topic = "machine/consumption/topic"
        mqtt_mediator = MqttMediator(self.machine_service_mock, self.mqtt_config_mock, Sources(consumption_topic),
                                     self.destinations_mock, self.mqtt_client_mock)
        self.mqtt_client_mock.subscribe = Mock()
        # when
        mqtt_mediator.start()
        # then
        self.mqtt_client_mock.subscribe.assert_called_with(consumption_topic, mqtt_mediator.power_consumption_update)

    def test_update_power_consumption(self):
        # given
        watt = 45.0
        msg = Mock(topic="some/topic", payload=str(watt))
        mqtt_mediator = MqttMediator(self.machine_service_mock, self.mqtt_config_mock, self.sources_mock,
                                     self.destinations_mock, self.mqtt_client_mock)
        self.machine_service_mock.update_power_consumption = Mock()
        # when
        mqtt_mediator.power_consumption_update(msg)
        # then
        self.machine_service_mock.update_power_consumption.assert_called_with(watt)

    def test_subscribes_for_un_loading_on_start(self):
        # given
        loading_topic = "loading/topic"
        unloading_topic = "unloading/topic"
        mqtt_mediator = MqttMediator(self.machine_service_mock, self.mqtt_config_mock, Sources(
            "machine/consumption/topic", loading_topic, unloading_topic),
                                     self.destinations_mock, self.mqtt_client_mock)
        self.mqtt_client_mock.subscribe = Mock()
        # when
        mqtt_mediator.start()
        # then
        self.mqtt_client_mock.subscribe.assert_any_call(loading_topic, mqtt_mediator.load_machine)
        self.mqtt_client_mock.subscribe.assert_any_call(unloading_topic, mqtt_mediator.unload_machine)

    def test_loading_machine(self):
        # given
        msg = Mock(topic="load/topic", payload=None)
        mqtt_mediator = MqttMediator(self.machine_service_mock, self.mqtt_config_mock, self.sources_mock,
                                     self.destinations_mock, self.mqtt_client_mock)
        self.machine_service_mock.loaded = Mock()
        # when
        mqtt_mediator.load_machine(msg)
        # then
        self.machine_service_mock.loaded.assert_called()

    def test_unloading_machine(self):
        # given
        msg = Mock(topic="unload/topic", payload=None)
        mqtt_mediator = MqttMediator(self.machine_service_mock, self.mqtt_config_mock, self.sources_mock,
                                     self.destinations_mock, self.mqtt_client_mock)
        self.machine_service_mock.unloaded = Mock()
        # when
        mqtt_mediator.unload_machine(msg)
        # then
        self.machine_service_mock.unloaded.assert_called()


if __name__ == '__main__':
    unittest.main()
