import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock, call, ANY

from waiting import wait

from iot.core.configuration import PlannedNotification, Destinations, Sources, MqttMeasureSource, Measure
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.machine.dryer import Dryer
from iot.infrastructure.machine.machine_service import MachineService
from iot.infrastructure.machine.machine_that_can_be_loaded import RunningState
from iot.infrastructure.machine.power_state_decorator import PowerState
from iot.infrastructure.thing import OnlineStatus
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_machine_mediator import MqttMachineMediator

DIR = Path(__file__).parent


def _set_up_croniter(responses: [datetime]):
    patcher = patch('iot.mqtt.mqtt_mediator.croniter')
    croniter_mock = patcher.start()
    croniter = Mock()
    croniter.get_next = Mock(side_effect=responses)
    croniter_mock.return_value = croniter


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

    def test_publishing_updates_when_specified_by_cron(self):
        # given
        destinations = Destinations(list([PlannedNotification("some/topic", "* * * * * *")]))
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock, self.sources_mock, destinations,
                                            self.mqtt_client_mock)
        _set_up_croniter(responses=[datetime.now(), datetime.now(), datetime.now() + timedelta(weeks=1)])
        # when
        mqtt_mediator.start()
        # then
        wait(lambda: sum(publish_args == call("some/topic", ANY) for publish_args in
                         self.mqtt_client_mock.publish.call_args_list) >= 2, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")

    def test_update_format_when_publishing(self):
        # given
        destinations = Destinations(list([PlannedNotification("some/topic", "* * * * * *")]))
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock, self.sources_mock, destinations,
                                            self.mqtt_client_mock)
        self._set_up_thing_matching_json_file()
        _set_up_croniter(responses=[datetime.now(), datetime.now() + timedelta(weeks=1)])
        # when
        mqtt_mediator.start()
        # then
        expected_json = json.loads(Path.open(DIR / "machine-update.json").read())
        # enums have to be converted
        expected_json['online_status'] = OnlineStatus(expected_json['online_status'])
        expected_json['power_state'] = PowerState(expected_json['power_state'])
        expected_json['running_state'] = RunningState(expected_json['running_state'])
        wait(lambda: sum(publish_args == call(ANY, ANY) for publish_args in
                         self.mqtt_client_mock.publish.call_args_list) >= 1, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")
        self.maxDiff = None
        self.assertDictEqual(expected_json, self.mqtt_client_mock.publish.call_args_list[0].args[1])

    def _set_up_thing_matching_json_file(self):
        # matches the values of the json file
        self.machine_service_mock.thing = Dryer("dryer", 2400.121, datetime.fromisoformat("2024-01-02T03:04:05.678910"),
                                                False, True, datetime.fromisoformat("2024-01-02T01:01:01.111111"),
                                                RunningState.RUNNING,
                                                datetime.fromisoformat("2023-12-31T23:59:02.133742"),
                                                datetime.fromisoformat("2024-01-02T03:04:05.678910"))

    def test_subscribes_for_consumption_on_start(self):
        # given
        consumption_topic = "machine/consumption/topic"
        self.mqtt_client_mock.subscribe = Mock()
        # when
        MqttMachineMediator(self.machine_service_mock,
                            Sources([MqttMeasureSource(consumption_topic, [Measure(source_type='consumption')])]),
                            self.destinations_mock,
                            self.mqtt_client_mock)
        # then
        self.mqtt_client_mock.subscribe.assert_called_with(consumption_topic, ANY)

    def test_update_power_consumption(self):
        # given
        watt = 45.0
        msg = Mock(topic="some/topic", payload=str(watt))
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock, self.sources_mock, self.destinations_mock,
                                            self.mqtt_client_mock)
        self.machine_service_mock.update_power_consumption = Mock()
        # when
        mqtt_mediator.power_consumption_update(msg)
        # then
        self.machine_service_mock.update_power_consumption.assert_called_with(watt)

    def test_subscribes_for_un_loading_on_start(self):
        # given
        loading_topic = "loading/topic"
        unloading_topic = "unloading/topic"
        self.mqtt_client_mock.subscribe = Mock()
        # when
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock,
                                            Sources([MqttMeasureSource(loading_topic, [Measure(source_type='loading')]),
                                                     MqttMeasureSource(unloading_topic, [Measure(source_type='unloading')])]),
                                            self.destinations_mock, self.mqtt_client_mock)
        # then
        self.mqtt_client_mock.subscribe.assert_any_call(loading_topic, mqtt_mediator.load_machine)
        self.mqtt_client_mock.subscribe.assert_any_call(unloading_topic, ANY)

    def test_loading_machine(self):
        # given
        msg = Mock(topic="load/topic", payload=None)
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock, self.sources_mock, self.destinations_mock,
                                            self.mqtt_client_mock)
        self.machine_service_mock.loaded = Mock()
        # when
        mqtt_mediator.load_machine(msg)
        # then
        self.machine_service_mock.loaded.assert_called()

    def test_loading_machine_needing_unload(self):
        # given
        msg = Mock(topic="load/topic", payload=str(True))
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock, self.sources_mock, self.destinations_mock,
                                            self.mqtt_client_mock)
        self.machine_service_mock.loaded = Mock()
        # when
        mqtt_mediator.load_machine(msg)
        # then
        self.machine_service_mock.loaded.assert_called_with(needs_unloading=True)

    def test_unloading_machine(self):
        # given
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock, self.sources_mock, self.destinations_mock,
                                            self.mqtt_client_mock)
        self.machine_service_mock.unloaded = Mock()
        # when
        mqtt_mediator.unload_machine()
        # then
        self.machine_service_mock.unloaded.assert_called()

    def test_handles_database_exceptions_without_breaking(self):
        mqtt_mediator = MqttMachineMediator(self.machine_service_mock, self.sources_mock, self.destinations_mock,
                                            self.mqtt_client_mock)

        self.machine_service_mock.unloaded = Mock(side_effect=DatabaseException)
        mqtt_mediator.unload_machine()

        self.machine_service_mock.loaded = Mock(side_effect=DatabaseException)
        mqtt_mediator.load_machine(Mock(topic="load/topic", payload=str(True)))

        self.machine_service_mock.update_power_consumption = Mock(side_effect=DatabaseException)
        mqtt_mediator.power_consumption_update(Mock(topic="some/topic", payload=str(45.0)))


if __name__ == '__main__':
    unittest.main()
