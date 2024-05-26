import unittest
from datetime import datetime

from iot.infrastructure.person import Person
from iot.infrastructure.register_of_persons import RegisterOfPersons


class TestRegisterOfPersons(unittest.TestCase):
    def setUp(self):
        """Prepare resources for testing."""
        self.register = RegisterOfPersons()
        self.sample_person = Person("John Doe")

    def test_enlist_new_person(self):
        """Test adding a new person to the register."""
        result = self.register.enlist(self.sample_person)
        self.assertIn(self.sample_person, self.register._persons)
        self.assertTrue(result)

    def test_enlist_existing_person_updates_info(self):
        """Test updating an existing person's details."""
        self.register.enlist(self.sample_person)
        updated_person = Person("John Doe", last_seen_at=datetime.now())
        self.register.enlist(updated_person)
        self.assertIn(updated_person, self.register._persons)
        self.assertEqual(len(self.register._persons), 1)  # Ensure no duplicate entries

    def test_dismiss_person(self):
        """Test removing a person by name."""
        self.register.enlist(self.sample_person)
        result = self.register.dismiss('John Doe')
        self.assertNotIn(self.sample_person, self.register._persons)
        self.assertTrue(result)

    def test_dismiss_person_not_found_returns_false(self):
        """Test dismiss returns False when person not found."""
        result = self.register.dismiss('Jane Doe')
        self.assertFalse(result)

    def test_locate_existing_person(self):
        """Test locating an existing person."""
        self.register.enlist(self.sample_person)
        person = self.register.locate('John Doe')
        self.assertEqual(person, self.sample_person)

    def test_locate_person_not_found_returns_none(self):
        """Test locating a non-existing person returns None."""
        person = self.register.locate('Jane Doe')
        self.assertIsNone(person)

    def test_catalog_all_returns_all_persons(self):
        """Test retrieving a list of all persons."""
        self.register.enlist(self.sample_person)
        another_person = Person('Jane Lime')
        self.register.enlist(another_person)
        all_persons = self.register.catalog_all()
        self.assertEqual(len(all_persons), 2)
        self.assertIn(self.sample_person, all_persons)
        self.assertIn(another_person, all_persons)


if __name__ == '__main__':
    unittest.main()
