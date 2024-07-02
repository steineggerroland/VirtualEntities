import unittest
from unittest.mock import MagicMock, call

from iot.core.storage import Storage
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.machine.washing_machine import WashingMachine


class TestApplianceDepot(unittest.TestCase):
    def setUp(self):
        self.storage_mock: Storage | MagicMock = MagicMock()
        self.time_series_storage: TimeSeriesStorage | MagicMock = MagicMock()
        self.depot = ApplianceDepot(self.storage_mock, self.time_series_storage)
        self.sample_appliance = WashingMachine("washer1", 'washing_machine')

    def test_stock_stores_new_appliance(self):
        """Test storing a new appliance."""
        self.storage_mock.update.return_value = False
        result = self.depot.stock(self.sample_appliance)
        self.storage_mock.update.assert_called_once_with(self.sample_appliance)
        self.assertFalse(result)

    def test_stock_updates_existing_appliance(self):
        """Test updating an existing appliance."""
        self.storage_mock.update.return_value = False
        self.depot.stock(self.sample_appliance)
        self.storage_mock.update.return_value = True
        updated_machine = WashingMachine("washer1", 233)
        result = self.depot.stock(updated_machine)
        self.storage_mock.update.assert_has_calls([call(self.sample_appliance), call(updated_machine)])
        self.assertTrue(result)

    def test_deplete_removes_appliance(self):
        """Test removing an appliance by name."""
        self.storage_mock.remove.return_value = True
        result = self.depot.deplete('washer1')
        self.storage_mock.remove.assert_called_once_with('washer1')
        self.assertTrue(result)

    def test_deplete_nonexistent_appliance(self):
        """Test attempt to remove an appliance that does not exist."""
        self.storage_mock.remove.return_value = False
        result = self.depot.deplete('nonexistent')
        self.assertFalse(result)

    def test_retrieve_appliance_details(self):
        """Test retrieving details of an appliance."""
        self.storage_mock.load_iot_machine.return_value = self.sample_appliance
        appliance = self.depot.retrieve('washer1')
        self.storage_mock.load_iot_machine.assert_called_once_with('washer1')
        self.assertEqual(appliance, self.sample_appliance)

    def test_inventory_lists_all_appliances(self):
        """Test listing all appliances in the depot."""
        self.storage_mock.load_all_iot_machines.return_value = [self.sample_appliance]
        inventory = self.depot.inventory()
        self.storage_mock.load_all_iot_machines.assert_called_once()
        self.assertIn(self.sample_appliance, inventory)


if __name__ == '__main__':
    unittest.main()
