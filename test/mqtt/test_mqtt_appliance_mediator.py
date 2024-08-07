import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock, call, ANY

from dateutil.tz import tzlocal
from waiting import wait

from iot.core.configuration import PlannedNotification, Destinations, Sources, MqttMeasureSource, Measure
from iot.infrastructure.appliance.appliance import RunningState
from iot.infrastructure.appliance.appliance_builder import ApplianceBuilder
from iot.infrastructure.appliance.appliance_service import ApplianceService
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.virtual_entity import OnlineStatus
from iot.mqtt.mqtt_appliance_mediator import MqttApplianceMediator
from iot.mqtt.mqtt_client import MqttClient

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
    @patch('iot.infrastructure.appliance.appliance_service.ApplianceService')
    def setUp(self, appliance_service_mock, mqtt_config_mock, sources_mock, destinations_mock, mqtt_client_mock):
        self.appliance_service_mock: Mock | ApplianceService = appliance_service_mock
        self.appliance_service_mock.entities.to_dict = Mock(return_value={})
        self.mqtt_config_mock = mqtt_config_mock
        self.sources_mock: Mock | Sources = sources_mock
        self.destinations_mock: Mock | Destinations = destinations_mock
        self.mqtt_client_mock: Mock | MqttClient = mqtt_client_mock
        self.appliance_name = 'some appliance'

    def test_publishing_updates_when_specified_by_cron(self):
        # given
        destinations = Destinations(list([PlannedNotification("some/topic", "* * * * * *")]))
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name, self.sources_mock, destinations)
        _set_up_croniter(
            responses=[datetime.now(tzlocal()), datetime.now(tzlocal()), datetime.now(tzlocal()) + timedelta(weeks=1)])
        # when
        mqtt_mediator.start()
        # then
        wait(lambda: sum(publish_args == call("some/topic", ANY) for publish_args in
                         self.mqtt_client_mock.publish.call_args_list) >= 2, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")

    def test_update_format_when_publishing(self):
        # given
        destinations = Destinations(list([PlannedNotification("some/topic", "* * * * * *")]))
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name, self.sources_mock, destinations)
        self._set_up_thing_matching_json_file()
        _set_up_croniter(responses=[datetime.now(tzlocal()), datetime.now(tzlocal()) + timedelta(weeks=1)])
        # when
        mqtt_mediator.start()
        # then
        expected_json = json.loads(Path.open(DIR / "appliance-update.json").read())
        # enums have to be converted
        expected_json['online_status'] = OnlineStatus(expected_json['online_status'])
        expected_json['power_state'] = PowerState(expected_json['power_state'])
        expected_json['running_state'] = RunningState(expected_json['running_state'])
        # all times are expected to be local timezone
        expected_json['started_run_at'] = datetime.fromisoformat(expected_json['started_run_at']).astimezone(
            tzlocal()).isoformat()
        expected_json['finished_last_run_at'] = datetime.fromisoformat(
            expected_json['finished_last_run_at']).astimezone(tzlocal()).isoformat()
        expected_json['last_seen_at'] = datetime.fromisoformat(expected_json['last_seen_at']).astimezone(
            tzlocal()).isoformat()
        expected_json['last_updated_at'] = datetime.fromisoformat(expected_json['last_updated_at']).astimezone(
            tzlocal()).isoformat()
        expected_json['is_loadable'] = True
        wait(lambda: sum(publish_args == call(ANY, ANY) for publish_args in
                         self.mqtt_client_mock.publish.call_args_list) >= 1, timeout_seconds=1,
             waiting_for="mqtt.publish called several times")
        self.maxDiff = None
        self.assertDictEqual(expected_json, self.mqtt_client_mock.publish.call_args_list[0].args[1])

    def _set_up_thing_matching_json_file(self):
        # matches the values of the json file
        self.appliance_service_mock.get_appliance = Mock(
            return_value=ApplianceBuilder.build_with(name="dryer", type="dryer", watt=2400.121,
                                                     last_seen_at=datetime.fromisoformat(
                                                         "2024-01-02T03:04:05.678910"),
                                                     needs_unloading=False, is_loaded=True,
                                                     is_loadable=True,
                                                     started_run_at=datetime.fromisoformat(
                                                         "2024-01-02T01:01:01.111111").astimezone(tzlocal()),
                                                     running_state=RunningState.RUNNING,
                                                     finished_last_run_at=datetime.fromisoformat(
                                                         "2023-12-31T23:59:02.133742").astimezone(tzlocal()),
                                                     last_updated_at=datetime.fromisoformat(
                                                         "2024-01-02T03:04:05.678910").astimezone(tzlocal())))

    def test_subscribes_for_consumption_on_start(self):
        # given
        consumption_topic = "appliance/consumption/topic"
        self.mqtt_client_mock.subscribe = Mock()
        # when
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name,
                                              Sources([MqttMeasureSource(consumption_topic,
                                                                         [Measure(source_type='consumption')])]),
                                              self.destinations_mock)
        # then
        self.mqtt_client_mock.subscribe.assert_called_with(self.appliance_name, consumption_topic, ANY)

    def test_update_power_consumption(self):
        # given
        watt = 45.0
        msg = Mock(topic="some/topic", payload=str(watt))
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name, self.sources_mock, self.destinations_mock)
        self.appliance_service_mock.update_power_consumption = Mock()
        # when
        mqtt_mediator.power_consumption_update(self.appliance_name, msg)
        # then
        self.appliance_service_mock.update_power_consumption.assert_called_with(self.appliance_name, watt)

    def test_subscribes_for_un_loading_on_start(self):
        # given
        loading_topic = "loading/topic"
        unloading_topic = "unloading/topic"
        self.mqtt_client_mock.subscribe = Mock()
        # when
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name,
                                              Sources(
                                                  [MqttMeasureSource(loading_topic, [Measure(source_type='loading')]),
                                                   MqttMeasureSource(unloading_topic,
                                                                     [Measure(source_type='unloading')])]),
                                              self.destinations_mock)
        # then
        self.mqtt_client_mock.subscribe.assert_any_call(self.appliance_name, loading_topic, ANY)
        self.mqtt_client_mock.subscribe.assert_any_call(self.appliance_name, unloading_topic, ANY)

    def test_loading_appliance(self):
        # given
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name, self.sources_mock, self.destinations_mock)
        msg = Mock(topic="load/topic", payload=None)
        self.appliance_service_mock.loaded = Mock()
        # when
        mqtt_mediator.load_appliance(self.appliance_name, msg)
        # then
        self.appliance_service_mock.loaded.assert_called()

    def test_loading_appliance_needing_unload(self):
        # given
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name, self.sources_mock, self.destinations_mock)
        msg = Mock(topic="load/topic", payload=str(True))
        self.appliance_service_mock.loaded = Mock()
        # when
        mqtt_mediator.load_appliance(self.appliance_name, msg)
        # then
        self.appliance_service_mock.loaded.assert_called_with(self.appliance_name, needs_unloading=True)

    def test_unloading_appliance(self):
        # given
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name, self.sources_mock, self.destinations_mock)
        self.appliance_service_mock.unloaded = Mock()
        # when
        mqtt_mediator.unload_appliance(self.appliance_name)
        # then
        self.appliance_service_mock.unloaded.assert_called()

    def test_handles_database_exceptions_without_breaking(self):
        mqtt_mediator = MqttApplianceMediator(self.appliance_service_mock, self.mqtt_client_mock)
        mqtt_mediator.add_appliance_by_config(self.appliance_name, self.sources_mock, self.destinations_mock)

        self.appliance_service_mock.unloaded = Mock(side_effect=DatabaseException)
        mqtt_mediator.unload_appliance(self.appliance_name)

        self.appliance_service_mock.loaded = Mock(side_effect=DatabaseException)
        mqtt_mediator.load_appliance(self.appliance_name, Mock(topic="load/topic", payload=str(True)))

        self.appliance_service_mock.update_power_consumption = Mock(side_effect=DatabaseException)
        mqtt_mediator.power_consumption_update(self.appliance_name, Mock(topic="some/topic", payload=str(45.0)))


if __name__ == '__main__':
    unittest.main()
