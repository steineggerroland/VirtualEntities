import unittest
from unittest.mock import MagicMock, Mock, call

from iot.core.storage import Storage
from iot.infrastructure.room import Room
from iot.infrastructure.room_catalog import RoomCatalog
from iot.infrastructure.units import Temperature


class TestRoomCatalog(unittest.TestCase):
    def setUp(self):
        self.storage_mock: MagicMock | Storage = MagicMock()
        self.room_catalog = RoomCatalog(self.storage_mock)
        self.sample_room = Room('Conference Room')

    def test_catalog_adds_room(self):
        """Test adding a room's details."""
        self.storage_mock.update.return_value = False
        result = self.room_catalog.catalog(self.sample_room)
        self.storage_mock.update.assert_called_once_with(self.sample_room)
        self.assertFalse(result)

    def test_catalog_updates_room(self):
        """Test adding or updating a room's details."""
        self.storage_mock.update.return_value = False
        self.room_catalog.catalog(self.sample_room)
        self.storage_mock.update.return_value = True
        updated_room = Room('Conference Room', Temperature(19.3), 66.6)
        result = self.room_catalog.catalog(updated_room)
        self.storage_mock.update.assert_has_calls([call(self.sample_room), call(updated_room)])
        self.assertTrue(result)

    def test_decommission_removes_room(self):
        """Test removing a room by name."""
        self.storage_mock.remove = Mock(return_value=True)
        result = self.room_catalog.decommission('Conference Room')
        self.storage_mock.remove.assert_called_once_with('Conference Room')
        self.assertTrue(result)

    def test_decommissioning_nonexistent_room(self):
        """Test removing a non-existing room."""
        self.storage_mock.remove = Mock(return_value=False)
        result = self.room_catalog.decommission('Conference Room')
        self.storage_mock.remove.assert_called_once_with('Conference Room')
        self.assertFalse(result)

    def test_find_room_retrieves_room_details(self):
        """Test retrieving a room's details by name."""
        self.storage_mock.load_room = Mock(return_value=self.sample_room)
        result = self.room_catalog.find_room('Conference Room')
        self.storage_mock.load_room.assert_called_once_with('Conference Room')
        self.assertEqual(self.sample_room, result)

    def test_list_all_rooms_lists_rooms(self):
        """Test listing all rooms."""
        self.storage_mock.load_all_rooms = Mock(return_value=[self.sample_room])
        result = self.room_catalog.list_all_rooms()
        self.storage_mock.load_all_rooms.assert_called_once()
        self.assertEqual([self.sample_room], result)


if __name__ == '__main__':
    unittest.main()
