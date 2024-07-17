import unittest
from datetime import datetime, timedelta

from dateutil.tz import tzlocal

from iot.infrastructure.person import Person
from iot.infrastructure.time.calendar import Calendar
from iot.infrastructure.virtual_entity import OnlineStatus


class PersonTest(unittest.TestCase):
    def test_to_dict(self):
        name = "Harry"
        last_updated_at = datetime.now(tzlocal()) - timedelta(minutes=23)
        last_seen_at = datetime.now(tzlocal())
        calendars = [Calendar("nextcloud", "nextcloud.url", "#FFFFF0"), Calendar("dav", "dav://url", "#F9F898")]
        person = Person(name, calendars, last_updated_at, last_seen_at)
        # when
        to_dict = person.to_dict()
        # then
        self.assertEqual(name, to_dict["name"])
        self.assertEqual(2, len(to_dict["calendars"]))
        self.assertEqual(OnlineStatus.ONLINE, to_dict["online_status"])
        self.assertEqual(last_updated_at.isoformat(), to_dict["last_updated_at"])
        self.assertEqual(last_seen_at.isoformat(), to_dict["last_seen_at"])


if __name__ == '__main__':
    unittest.main()
