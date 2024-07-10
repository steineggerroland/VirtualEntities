import unittest
from unittest.mock import Mock

from iot.core.configuration import VirtualEntityConfig, UrlConf, Sources, CaldavConfig
from iot.infrastructure.person_service import PersonService


class PersonServiceCase(unittest.TestCase):
    def test_constructor(self):
        name = "mika"
        register_of_persons_mock = Mock()
        PersonService(register_of_persons_mock,
                      VirtualEntityConfig(name, sources=Sources(
                          [CaldavConfig(UrlConf("calendar", "my cal", "calendar.url"), "999999")])))
        registered_person = register_of_persons_mock.enlist.call_args[0][0]
        self.assertEqual(name, registered_person.name)
        self.assertEqual(1, len(registered_person.calendars))
        self.assertEqual("my cal", registered_person.calendars[0].name)
        self.assertEqual("calendar.url", registered_person.calendars[0].url)
        self.assertEqual("999999", registered_person.calendars[0].color)
        self.assertListEqual([], registered_person.calendars[0].appointments)


if __name__ == '__main__':
    unittest.main()
