import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from iot.core.Storage import Storage
from iot.infrastructure.machine.MachineService import MachineService, DatabaseException
from iot.infrastructure.machine.WashingMachine import WashingMachine


class InitTest(unittest.TestCase):
    def test_init(self):
        configuration_mock = Mock(type='washing_machine')
        storage_mock = Mock()
        storage_mock.load_thing = Mock(return_value={'name': 'washing_machine'})
        machine_service = MachineService(storage_mock, configuration_mock)
        self.assertIsInstance(machine_service.thing, WashingMachine)
        self.assertIsNotNone(machine_service.storage)
        self.assertIsNotNone(machine_service.logger)

    def test_start_run_initiated(self):
        # given
        configuration_mock = Mock(type='dryer')
        storage_mock = Mock()
        patcher = patch('iot.infrastructure.machine.MachineService.d_from_dict')
        croniter_mock = patcher.start()
        washing_machine_mock = Mock()
        croniter_mock.return_value = washing_machine_mock
        washing_machine_mock.started_run_at = datetime.now()
        # when
        MachineService(storage_mock, configuration_mock)
        # then
        washing_machine_mock.start_run.assert_called()


class MachinePowerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration_mock: Mock | Storage = Mock(type='washing_machine')
        self.storage_mock: Mock | Storage = Mock()
        self.storage_mock.load_thing = Mock(return_value={'name': 'washing_machine'})
        self.machine_service = MachineService(self.storage_mock, self.configuration_mock)

    def test_update_power_consumption(self):
        # given
        watt = 1898
        self.machine_service.thing.update_power_consumption = Mock()
        self.storage_mock.update_thing = Mock()
        self.storage_mock.append_power_consumption = Mock()
        # when
        self.machine_service.update_power_consumption(watt)
        # then
        self.machine_service.thing.update_power_consumption.assert_called_once_with(watt)
        self.storage_mock.update_thing.assert_called_once_with(self.machine_service.thing)
        self.storage_mock.append_power_consumption.assert_called_once_with(watt, self.machine_service.thing.name)

    def test_started_run_called_on_change_to_running(self):
        # given
        self.machine_service.thing.start_run = Mock()
        self.machine_service.thing.started_run_at = None
        watt_indicating_run = 1898
        # when
        self.machine_service.update_power_consumption(watt_indicating_run)
        # then
        self.machine_service.thing.start_run.assert_called()

    def test_started_run_not_called_when_already_running(self):
        # given
        self.machine_service.thing.start_run = Mock()
        self.machine_service.thing.started_run_at = datetime.now()
        watt_indicating_run = 1898
        # when
        self.machine_service.update_power_consumption(watt_indicating_run)
        # then
        self.machine_service.thing.start_run.assert_not_called()

    def test_start_run(self):
        # given
        self.storage_mock.update_thing = Mock()
        self.machine_service.thing.started_run_at = None
        self.machine_service._scheduled_check = Mock()  # avoid check causing errors
        # when
        self.machine_service.started_run()
        # then
        self.assertAlmostEqual(self.machine_service.thing.started_run_at, datetime.now(), delta=timedelta(seconds=0.1))
        self.storage_mock.update_thing.assert_called_once_with(self.machine_service.thing)

    def test_start_run_schedules_finish_check(self):
        # given
        self.machine_service._scheduled_check = Mock()
        self.machine_service.thing.started_run_at = None
        # when
        self.machine_service.started_run()
        # then
        self.machine_service._scheduled_check.assert_called()

    def test_finished_run(self):
        # given
        self.machine_service.thing.finish_run = Mock()
        self.storage_mock.update_thing = Mock()
        # when
        self.machine_service.finished_run()
        # then
        self.machine_service.thing.finish_run.assert_called()
        self.storage_mock.update_thing.assert_called()

    def test_unloaded(self):
        # given
        self.machine_service.thing.unload = Mock()
        self.storage_mock.update_thing = Mock()
        # when
        self.machine_service.unloaded()
        # then
        self.machine_service.thing.unload.assert_called()
        self.storage_mock.update_thing.assert_called()

    def test_loaded(self):
        # given
        self.machine_service.thing.load = Mock()
        self.storage_mock.update_thing = Mock()
        # when
        self.machine_service.loaded()
        # then
        self.machine_service.thing.load.assert_called()
        self.storage_mock.update_thing.assert_called()


class DatabaseExceptionTranslationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration_mock: Mock | Storage = Mock(type='washing_machine')
        self.storage_mock: Mock | Storage = Mock()
        self.storage_mock.load_thing = Mock(return_value={'name': 'washing_machine'})
        self.machine_service = MachineService(self.storage_mock, self.configuration_mock)
        self.storage_mock.update_thing.side_effect = [ValueError()]

    def test_update_power_consumption(self):
        self.assertRaises(DatabaseException, self.machine_service.update_power_consumption, 14)

    def test_started_run(self):
        self.assertRaises(DatabaseException, self.machine_service.started_run)

    def test_finished_run(self):
        self.assertRaises(DatabaseException, self.machine_service.finished_run)

    def test_loaded(self):
        self.assertRaises(DatabaseException, self.machine_service.loaded)

    def test_unloaded(self):
        self.assertRaises(DatabaseException, self.machine_service.unloaded)


if __name__ == '__main__':
    unittest.main()
