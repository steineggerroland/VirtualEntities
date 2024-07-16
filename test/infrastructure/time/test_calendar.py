import unittest
from datetime import datetime, timedelta

import pytz

from iot.infrastructure.virtual_entity import OnlineStatus
from iot.infrastructure.time.calendar import Appointment, Calendar


class CalendarTest(unittest.TestCase):
    def test_get_appointments(self):
        now = datetime.now().astimezone(pytz.timezone("Europe/Berlin"))
        start = now
        appointments = [Appointment("", now - timedelta(days=1, hours=1), now - timedelta(days=1), "123123"),
                        Appointment("", now + timedelta(days=1), now + timedelta(days=1, hours=1), "123123"),
                        Appointment("", now - timedelta(minutes=30), now + timedelta(minutes=30), "123123")]
        calendar = Calendar("nextcloud", "url", "123123", appointments)

        self.assertEqual(1, len(calendar.find_appointments(start, timedelta(hours=1))))

    def test_to_dict(self):
        appointments = [Appointment("Free time just for me", datetime.fromisoformat("2020-01-24T13:00:00"),
                                    datetime.fromisoformat("2020-01-24T15:00:00"), "FF0000"),
                        Appointment("Meeting", datetime.fromisoformat("2020-02-01T10:00:00"),
                                    datetime.fromisoformat("2020-02-01T10:30:00"), "00ff00"),
                        Appointment("Holidays", datetime.fromisoformat("2020-05-10T00:00:00"),
                                    datetime.fromisoformat("2020-05-15T00:00:00"), "0000ff")]
        name = "nextcloud"
        url = "url"
        color = "ff0000"
        last_updated_at = datetime.now() - timedelta(minutes=23)
        last_seen_at = datetime.now()
        calendar = Calendar(name, url, color, appointments, last_updated_at, last_seen_at)
        # then
        self.assertIn("appointments", calendar.to_dict())
        self.assertEqual(3, len(calendar.to_dict()["appointments"]))
        self.assertEqual(name, calendar.to_dict()["name"])
        self.assertEqual(url, calendar.to_dict()["url"])
        self.assertEqual(OnlineStatus.ONLINE, calendar.to_dict()["online_status"])
        self.assertEqual(last_seen_at.isoformat(), calendar.to_dict()["last_seen_at"])
        self.assertEqual(last_updated_at.isoformat(), calendar.to_dict()["last_updated_at"])
        self.assertEqual(color, calendar.to_dict()["color"])


class AppointmentTest(unittest.TestCase):
    def test_constructor(self):
        appointment = Appointment("Free time just for me", datetime.fromisoformat("2020-01-24T13:00:00").astimezone(
            pytz.timezone("Europe/Berlin")), datetime.fromisoformat("2020-01-24T15:00:00").astimezone(
            pytz.timezone("Europe/Berlin")), "123123")
        self.assertEqual(appointment.summary, "Free time just for me")
        self.assertEqual(appointment.start_at, datetime.fromisoformat("2020-01-24T13:00:00").astimezone(
            pytz.timezone("Europe/Berlin")))
        self.assertEqual(appointment.end_at, datetime.fromisoformat("2020-01-24T15:00:00").astimezone(
            pytz.timezone("Europe/Berlin")))
        self.assertEqual(appointment.color, "123123")

    def test_covers_testcases(self):
        now = datetime.now()
        start = now
        end = now + timedelta(hours=1)
        tests = [{"description": "is_before_time_interval",
                  "appointment": Appointment("", now - timedelta(days=1, hours=1), now - timedelta(days=1), "123123"),
                  "expectation": False},
                 {"description": "is_after_time_interval",
                  "appointment": Appointment("", now + timedelta(days=1), now + timedelta(days=1, hours=1), "123123"),
                  "expectation": False},
                 {"description": "starts_before_and_ends_in_time_interval",
                  "appointment": Appointment("", now - timedelta(minutes=30), now + timedelta(minutes=30), "123123"),
                  "expectation": True},
                 {"description": "is_in_time_interval",
                  "appointment": Appointment("", now + timedelta(minutes=15), now + timedelta(minutes=45), "123123"),
                  "expectation": True},
                 {"description": "starts_in_and_ends_after_time_interval",
                  "appointment": Appointment("", now + timedelta(minutes=30), now + timedelta(hours=1, minutes=30),
                                             "123123"),
                  "expectation": True}]
        for test in tests:
            with self.subTest(test["description"]):
                self.assert_covers_parametrized(start, end, test["appointment"], test["expectation"])

    def assert_covers_parametrized(self, start: datetime, end: datetime, appointment: Appointment, expectation: bool):
        self.assertEqual(appointment.covers_interval(start, end), expectation,
                         "Expecting appointment (start: %s, end: %s) %s to cover time interval start: %s, end: %s." % (
                             appointment.start_at, appointment.end_at, "" if expectation else "not", start, end))

    def test_to_dict(self):
        summary = "Free time just for me"
        start = datetime.fromisoformat("2020-01-24T13:00:00").astimezone(pytz.timezone("Europe/Berlin"))
        end = datetime.fromisoformat("2020-01-24T15:00:00").astimezone(pytz.timezone("Europe/Berlin"))
        color = "ff0000"
        last_updated_at = datetime.fromisoformat("2020-01-24T15:00:00")
        appointment = Appointment(summary, start, end, color)
        appointment.last_updated_at = last_updated_at
        # then
        self.assertDictEqual(appointment.to_dict(), {"summary": summary,
                                                     "start_at": start.isoformat(),
                                                     "end_at": end.isoformat(),
                                                     "color": color,
                                                     "last_updated_at": last_updated_at.isoformat()})


if __name__ == '__main__':
    unittest.main()
