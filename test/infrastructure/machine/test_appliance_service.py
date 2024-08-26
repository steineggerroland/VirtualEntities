import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, ANY

from dateutil.tz import tzlocal

from iot.core.configuration import VirtualEntityConfig
from iot.core.configuration_manager import ConfigurationManager
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.appliance.appliance import Appliance
from iot.infrastructure.appliance.appliance_builder import ApplianceBuilder
from iot.infrastructure.appliance.appliance_depot import ApplianceDepot
from iot.infrastructure.appliance.appliance_service import ApplianceService, DatabaseException


class InitTest(unittest.TestCase):
    def test_init(self):
        configuration_mock = Mock(wraps=VirtualEntityConfig(name='washing_machine', entity_type='washing_machine'))
        storage_mock = Mock()
        storage_mock.load_entity = Mock(
            return_value=ApplianceBuilder.build_with(name='washing_machine', type='washing_machine'))
        test = storage_mock.load_entity('washing_machine')
        time_series_storage_mock = TimeSeriesStorage()
        configuration_manager_mock = ConfigurationManager()
        appliance_service = ApplianceService(ApplianceDepot(storage_mock, time_series_storage_mock),
                                             time_series_storage_mock, configuration_manager_mock)
        self.assertIsNotNone(appliance_service.time_series_storage)
        self.assertIsNotNone(appliance_service.appliance_depot)
        self.assertIsNotNone(appliance_service.logger)

    def test_start_run_initiated(self):
        # given
        configuration_mock = Mock(wraps=VirtualEntityConfig(name='Dryer', entity_type='dryer'))
        dryer_mock = Mock(
            wraps=ApplianceBuilder.build_with(name='Dryer', type='dryer', started_run_at=datetime.now(tzlocal())))
        storage_mock = Mock()
        storage_mock.load_appliance = Mock(return_value=dryer_mock)
        time_series_storage_mock = TimeSeriesStorage()
        configuration_manager_mock = ConfigurationManager()
        # when
        service = ApplianceService(ApplianceDepot(storage_mock, time_series_storage_mock), time_series_storage_mock,
                                   configuration_manager_mock)
        service.add_appliance_by_config([configuration_mock])
        # then
        dryer_mock.start_run.assert_called()


class AppliancePowerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.entity_name = "some entity"
        self.entity: Appliance = ApplianceBuilder.build_with(name=self.entity_name, type='washing_machine')
        self.configuration_mock: Mock | VirtualEntityConfig = Mock(
            wraps=VirtualEntityConfig(name=self.entity_name, entity_type='washing_machine'))
        self.configuration_mock.name = self.entity_name
        self.appliance_depot_mock: Mock | ApplianceDepot = Mock()
        self.appliance_depot_mock.retrieve = Mock(return_value=self.entity)
        self.configuration_manager_mock = Mock()
        self.time_series_storage_mock = Mock()
        self.appliance_service = ApplianceService(self.appliance_depot_mock,
                                                  self.time_series_storage_mock, self.configuration_manager_mock)
        self.appliance_service.add_appliance_by_config([self.configuration_mock])

    def test_update_power_consumption(self):
        # given
        watt = 0.1337
        self.appliance_depot_mock.stock = Mock()
        self.time_series_storage_mock.append_power_consumption = Mock()
        self.entity.update_power_consumption = Mock(wraps=self.entity.update_power_consumption)
        # when
        self.appliance_service.update_power_consumption(self.entity_name, watt)
        # then
        self.entity.update_power_consumption.assert_called_once_with(watt)
        self.appliance_depot_mock.stock.assert_called_once()
        self.time_series_storage_mock.append_power_consumption.assert_called_once_with(ANY, self.entity_name)

    def test_started_run_called_on_change_to_running(self):
        # given
        self.entity.start_run = Mock()
        self.entity.started_run_at = None
        watt_indicating_run = 1894
        # when
        self.appliance_service.update_power_consumption(self.entity_name, watt_indicating_run)
        # then
        self.entity.start_run.assert_called()

    def test_started_run_not_called_when_already_running(self):
        # given
        self.entity.start_run = Mock()
        self.entity.started_run_at = datetime.now(tzlocal())
        self.entity.start_run = Mock()
        watt_indicating_run = 1894
        # when
        self.appliance_service.update_power_consumption(self.entity_name, watt_indicating_run)
        # then
        self.entity.start_run.assert_not_called()

    def test_start_run(self):
        # given
        self.appliance_depot_mock.stock = Mock()
        self.entity.started_run_at = None
        self.appliance_service._scheduled_check = Mock()  # avoid check causing errors
        # when
        self.appliance_service.start_run(self.entity_name)
        # then
        self.assertAlmostEqual(self.entity.started_run_at, datetime.now(tzlocal()), delta=timedelta(seconds=0.1))
        self.appliance_depot_mock.stock.assert_called_once_with(self.entity)

    def test_start_run_schedules_finish_check(self):
        # given
        self.appliance_service._scheduled_check = Mock()
        self.entity.started_run_at = None
        # when
        self.appliance_service.start_run(self.entity_name)
        # then
        self.appliance_service._scheduled_check.assert_called()

    def test_finished_run(self):
        # given
        self.entity.finish_run = Mock(return_value=self.entity)
        self.entity.started_run_at = datetime.now(tzlocal())
        self.entity.finished_last_run_at = None
        self.appliance_depot_mock.stock = Mock()
        # when
        self.appliance_service.finish_run(self.entity_name)
        # then
        self.entity.finish_run.assert_called()
        self.appliance_depot_mock.stock.assert_called()

    def test_unloaded(self):
        # given
        self.entity.unload = Mock()
        self.appliance_depot_mock.stock = Mock()
        # when
        self.appliance_service.unloaded(self.entity_name)
        # then
        self.entity.unload.assert_called()
        self.appliance_depot_mock.stock.assert_called()

    def test_loaded(self):
        # given
        self.entity.load = Mock()
        self.appliance_depot_mock.stock = Mock()
        # when
        self.appliance_service.loaded(self.entity_name)
        # then
        self.entity.load.assert_called()
        self.appliance_depot_mock.stock.assert_called()

    def test_loaded_needing_unload(self):
        # given
        self.entity.load = Mock()
        self.appliance_depot_mock.stock = Mock()
        # when
        self.appliance_service.loaded(self.entity_name, needs_unloading=True)
        # then
        self.entity.load.assert_called_with(True)
        self.appliance_depot_mock.stock.assert_called()


class ChargeableApplianceInitTest(unittest.TestCase):
    def test_appliance_init_as_chargeable(self):
        configuration: VirtualEntityConfig = VirtualEntityConfig(name='some name',
                                                                 entity_type='washing_machine',
                                                                 power_consumption_indicates_charging=True)
        appliance_depot_mock: Mock | ApplianceDepot = Mock()
        appliance_depot_mock.retrieve = Mock(return_value=None)
        appliance_service = ApplianceService(appliance_depot_mock, Mock(), Mock())
        appliance_depot_mock.stock = Mock()
        # when
        appliance_service.add_appliance_by_config([configuration])
        # then
        appliance_depot_mock.stock.assert_called()
        saved_appliance = appliance_depot_mock.stock.call_args[0][0]
        self.assertEqual(saved_appliance.power_consumption_indicates_charging, True)

    def test_config_overrides_database_when_chargeable(self):
        entity_name = "some entity"
        entity = ApplianceBuilder.build_with(name=entity_name, type='washing_machine')
        configuration: VirtualEntityConfig = VirtualEntityConfig(name=entity_name,
                                                                 entity_type='washing_machine',
                                                                 power_consumption_indicates_charging=True)
        appliance_depot_mock: Mock | ApplianceDepot = Mock()
        appliance_depot_mock.retrieve = Mock(return_value=entity)
        appliance_service = ApplianceService(appliance_depot_mock, Mock(), Mock())
        appliance_depot_mock.stock = Mock()
        # when
        appliance_service.add_appliance_by_config([configuration])
        # then
        appliance_depot_mock.stock.assert_called()
        saved_appliance = appliance_depot_mock.stock.call_args[0][0]
        self.assertEqual(saved_appliance.power_consumption_indicates_charging, True)


class ChargeableApplianceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.entity_name = "some entity"
        self.entity: Appliance = ApplianceBuilder.build_with(name=self.entity_name, type='washing_machine')
        self.configuration_mock: Mock | VirtualEntityConfig = Mock(
            wraps=VirtualEntityConfig(name=self.entity_name, entity_type='washing_machine',
                                      power_consumption_indicates_charging=True))
        self.configuration_mock.name = self.entity_name
        self.appliance_depot_mock: Mock | ApplianceDepot = Mock()
        self.appliance_depot_mock.retrieve = Mock(return_value=self.entity)
        self.configuration_manager_mock = Mock()
        self.time_series_storage_mock = Mock()
        self.appliance_service = ApplianceService(self.appliance_depot_mock,
                                                  self.time_series_storage_mock, self.configuration_manager_mock)
        self.appliance_service.add_appliance_by_config([self.configuration_mock])

    def test_update_power_consumption(self):
        # given
        watt = 0.1337
        self.appliance_depot_mock.stock = Mock()
        self.time_series_storage_mock.append_power_consumption = Mock()
        self.entity.update_power_consumption = Mock(wraps=self.entity.update_power_consumption)
        # when
        self.appliance_service.update_power_consumption(self.entity_name, watt)
        # then
        self.entity.update_power_consumption.assert_called_once_with(watt)
        self.appliance_depot_mock.stock.assert_called_once()
        self.time_series_storage_mock.append_power_consumption.assert_called_once_with(ANY, self.entity_name)

    def test_started_run_called_on_change_to_running(self):
        # given
        self.entity.start_run = Mock()
        self.entity.started_run_at = None
        watt_indicating_run = 1894
        # when
        self.appliance_service.update_power_consumption(self.entity_name, watt_indicating_run)
        # then
        self.entity.start_run.assert_called()

    def test_started_run_not_called_when_already_running(self):
        # given
        self.entity.start_run = Mock()
        self.entity.started_run_at = datetime.now(tzlocal())
        self.entity.start_run = Mock()
        watt_indicating_run = 1894
        # when
        self.appliance_service.update_power_consumption(self.entity_name, watt_indicating_run)
        # then
        self.entity.start_run.assert_not_called()

    def test_start_run(self):
        # given
        self.appliance_depot_mock.stock = Mock()
        self.entity.started_run_at = None
        self.appliance_service._scheduled_check = Mock()  # avoid check causing errors
        # when
        self.appliance_service.start_run(self.entity_name)
        # then
        self.assertAlmostEqual(self.entity.started_run_at, datetime.now(tzlocal()), delta=timedelta(seconds=0.1))
        self.appliance_depot_mock.stock.assert_called_once_with(self.entity)

    def test_start_run_schedules_finish_check(self):
        # given
        self.appliance_service._scheduled_check = Mock()
        self.entity.started_run_at = None
        # when
        self.appliance_service.start_run(self.entity_name)
        # then
        self.appliance_service._scheduled_check.assert_called()

    def test_finished_run(self):
        # given
        self.entity.finish_run = Mock(return_value=self.entity)
        self.entity.started_run_at = datetime.now(tzlocal())
        self.entity.finished_last_run_at = None
        self.appliance_depot_mock.stock = Mock()
        # when
        self.appliance_service.finish_run(self.entity_name)
        # then
        self.entity.finish_run.assert_called()
        self.appliance_depot_mock.stock.assert_called()


class DatabaseExceptionTranslationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration_mock: Mock | VirtualEntityConfig = Mock(type='washing_machine')
        self.appliance_depot_mock: Mock | ApplianceDepot = Mock()
        self.appliance_depot_mock.retrieve = Mock(
            return_value=ApplianceBuilder.build_with(name='washing_machine', type='washing_machine', is_loadable=True))
        self.time_series_storage = MagicMock()
        self.configuration_manager = MagicMock()
        self.appliance_service = ApplianceService(self.appliance_depot_mock, self.time_series_storage,
                                                  self.configuration_manager)
        self.appliance_service.add_appliance_by_config([self.configuration_mock])
        self.appliance_depot_mock.stock.side_effect = [ValueError()]

    def test_update_power_consumption(self):
        self.assertRaises(DatabaseException, self.appliance_service.update_power_consumption, 'washing_machine', 14)

    def test_started_run(self):
        self.assertRaises(DatabaseException, self.appliance_service.start_run, 'washing_machine')

    def test_finished_run(self):
        self.assertRaises(DatabaseException, self.appliance_service.finish_run, 'washing_machine')

    def test_loaded(self):
        self.assertRaises(DatabaseException, self.appliance_service.loaded, 'washing_machine')

    def test_unloaded(self):
        self.assertRaises(DatabaseException, self.appliance_service.unloaded, 'washing_machine')


if __name__ == '__main__':
    unittest.main()
