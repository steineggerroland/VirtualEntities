import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from iot.core.configuration import ConfigurationManager, IotThingConfig
from iot.core.storage import Storage
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.machine.machine_service import MachineService, DatabaseException
from iot.infrastructure.machine.washing_machine import WashingMachine


class InitTest(unittest.TestCase):
    def test_init(self):
        configuration_mock = Mock(type='washing_machine')
        configuration_mock.name = 'washing machine'
        storage_mock = Mock()
        storage_mock.load_thing = Mock(return_value=WashingMachine('washing_machine', 'washing_machine'))
        time_series_storage_mock = TimeSeriesStorage()
        configuration_manager_mock = ConfigurationManager()
        machine_service = MachineService(ApplianceDepot(storage_mock, time_series_storage_mock),storage_mock,
                                         time_series_storage_mock, configuration_manager_mock)
        machine_service.add_machines_by_config([configuration_mock])
        self.assertIsNotNone(machine_service.time_series_storage)
        self.assertIsNotNone(machine_service.appliance_depot)
        self.assertIsNotNone(machine_service.logger)

    def test_start_run_initiated(self):
        # given
        configuration_mock = Mock(type='dryer')
        dryer_mock = Mock()
        storage_mock = Mock()
        storage_mock.load_iot_machine = Mock(return_value=dryer_mock)
        dryer_mock.started_run_at = datetime.now()
        time_series_storage_mock = TimeSeriesStorage()
        configuration_manager_mock = ConfigurationManager()
        # when
        service = MachineService(ApplianceDepot(storage_mock, time_series_storage_mock), storage_mock,time_series_storage_mock,
                       configuration_manager_mock)
        service.add_machines_by_config([configuration_mock])
        # then
        dryer_mock.start_run.assert_called()


class MachinePowerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.thing_name = "some thing"
        self.thing: WashingMachine = WashingMachine(self.thing_name, 'washing_machine')
        self.configuration_mock: Mock | IotThingConfig = MagicMock(type='washing_machine')
        self.configuration_mock.name = self.thing_name
        self.storage_mock: Mock | Storage = Mock()
        self.storage_mock.load_iot_machine = Mock(return_value=self.thing)
        self.configuration_manager_mock = Mock()
        self.time_series_storage_mock = Mock()
        self.machine_service = MachineService(ApplianceDepot(self.storage_mock, self.time_series_storage_mock),
                                              self.storage_mock, self.time_series_storage_mock,
                                              self.configuration_manager_mock)
        self.machine_service.add_machines_by_config([self.configuration_mock])

    def test_update_power_consumption(self):
        # given
        watt = 1898
        self.storage_mock.update = Mock()
        self.time_series_storage_mock.append_power_consumption = Mock()
        self.thing.update_power_consumption = Mock()
        # when
        self.machine_service.update_power_consumption(self.thing_name, watt)
        # then
        self.thing.update_power_consumption.assert_called_once_with(watt)
        self.storage_mock.update.assert_called_once()
        self.time_series_storage_mock.append_power_consumption.assert_called_once_with(watt, self.thing_name)

    def test_started_run_called_on_change_to_running(self):
        # given
        self.thing.start_run = Mock()
        self.thing.started_run_at = None
        watt_indicating_run = 1898
        # when
        self.machine_service.update_power_consumption(self.thing_name, watt_indicating_run)
        # then
        self.thing.start_run.assert_called()

    def test_started_run_not_called_when_already_running(self):
        # given
        self.thing.start_run = Mock()
        self.thing.started_run_at = datetime.now()
        self.thing.start_run = Mock()
        watt_indicating_run = 1898
        # when
        self.machine_service.update_power_consumption(self.thing_name, watt_indicating_run)
        # then
        self.thing.start_run.assert_not_called()

    def test_start_run(self):
        # given
        self.storage_mock.update = Mock()
        self.thing.started_run_at = None
        self.machine_service._scheduled_check = Mock()  # avoid check causing errors
        # when
        self.machine_service.started_run(self.thing_name)
        # then
        self.assertAlmostEqual(self.thing.started_run_at, datetime.now(), delta=timedelta(seconds=0.1))
        self.storage_mock.update.assert_called_once_with(self.thing)

    def test_start_run_schedules_finish_check(self):
        # given
        self.machine_service._scheduled_check = Mock()
        self.thing.started_run_at = None
        # when
        self.machine_service.started_run(self.thing_name)
        # then
        self.machine_service._scheduled_check.assert_called()

    def test_finished_run(self):
        # given
        self.thing.finish_run = Mock()
        self.storage_mock.update = Mock()
        # when
        self.machine_service.finished_run(self.thing_name)
        # then
        self.thing.finish_run.assert_called()
        self.storage_mock.update.assert_called()

    def test_unloaded(self):
        # given
        self.thing.unload = Mock()
        self.storage_mock.update = Mock()
        # when
        self.machine_service.unloaded(self.thing_name)
        # then
        self.thing.unload.assert_called()
        self.storage_mock.update.assert_called()

    def test_loaded(self):
        # given
        self.thing.load = Mock()
        self.storage_mock.update = Mock()
        # when
        self.machine_service.loaded(self.thing_name)
        # then
        self.thing.load.assert_called()
        self.storage_mock.update.assert_called()

    def test_loade_needing_unload(self):
        # given
        self.thing.load = Mock()
        self.storage_mock.update = Mock()
        # when
        self.machine_service.loaded(self.thing_name, needs_unloading=True)
        # then
        self.thing.load.assert_called_with(True)
        self.storage_mock.update.assert_called()


class DatabaseExceptionTranslationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration_mock: Mock | IotThingConfig = Mock(type='washing_machine')
        self.storage_mock: Mock | Storage = Mock()
        self.storage_mock.load_iot_machine = Mock(return_value=WashingMachine('washing_machine', 'washing_machine'))
        self.time_series_storage = MagicMock()
        self.configuration_manager = MagicMock()
        self.machine_service = MachineService(ApplianceDepot(self.storage_mock, self.time_series_storage),self.storage_mock,
                                              self.time_series_storage, self.configuration_manager)
        self.machine_service.add_machines_by_config([self.configuration_mock])
        self.storage_mock.update.side_effect = [ValueError()]

    def test_update_power_consumption(self):
        self.assertRaises(DatabaseException, self.machine_service.update_power_consumption, 'washing_machine', 14)

    def test_started_run(self):
        self.assertRaises(DatabaseException, self.machine_service.started_run, 'washing_machine')

    def test_finished_run(self):
        self.assertRaises(DatabaseException, self.machine_service.finished_run, 'washing_machine')

    def test_loaded(self):
        self.assertRaises(DatabaseException, self.machine_service.loaded, 'washing_machine')

    def test_unloaded(self):
        self.assertRaises(DatabaseException, self.machine_service.unloaded, 'washing_machine')


if __name__ == '__main__':
    unittest.main()
