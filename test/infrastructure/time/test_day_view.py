import unittest
from datetime import date, datetime

from iot.infrastructure.time.calendar import Appointment, Calendar
from iot.infrastructure.time.day_view import project_day


def event(start, end, title='Normal'):
    return Appointment(title, datetime.fromisoformat(start), datetime.fromisoformat(end), '00ff00')


class DayViewTest(unittest.TestCase):
    def test_exact_boundaries_and_priority_independent_of_order(self):
        normal = event('2026-09-11T09:00:00+02:00', '2026-09-11T11:00:00+02:00')
        important = event('2026-09-11T10:30:00+02:00', '2026-09-11T11:00:00+02:00', 'Wichtig: Arzt')
        expected = [None] * 24
        expected[9:11] = ['ffffff', 'ff0000']
        for appointments in ([normal, important], [important, normal]):
            self.assertEqual(expected, project_day(appointments, date(2026, 9, 11)))

    def test_all_day_preserved_but_ignored_by_board(self):
        appointment = Appointment('Wichtig: Urlaub', date(2026, 9, 11), date(2026, 9, 12), 'ff0000')
        self.assertEqual('2026-09-11', appointment.to_dict()['start_at'])
        self.assertEqual([None] * 24, project_day([appointment], date(2026, 9, 11)))
        self.assertFalse(appointment.covers_interval(datetime(2026, 9, 12), datetime(2026, 9, 13)))

    def test_midnight_and_zero_duration(self):
        appointment = event('2026-09-10T23:30:00+02:00', '2026-09-11T00:30:00+02:00')
        point = event('2026-09-11T10:30:00+02:00', '2026-09-11T10:30:00+02:00')
        self.assertEqual(['ffffff'] + [None] * 23, project_day([appointment, point], date(2026, 9, 11)))

    def test_spring_missing_hour(self):
        appointment = event('2026-03-29T01:00:00+01:00', '2026-03-29T04:00:00+02:00')
        slots = project_day([appointment], date(2026, 3, 29))
        self.assertEqual(['ffffff', None, 'ffffff', None], slots[1:5])

    def test_autumn_repeated_hour(self):
        first = event('2026-10-25T02:00:00+02:00', '2026-10-25T02:30:00+02:00')
        second = event('2026-10-25T02:00:00+01:00', '2026-10-25T02:30:00+01:00', 'Wichtig: Zweite Stunde')
        slots = project_day([first, second], date(2026, 10, 25))
        self.assertEqual('ff0000', slots[2])
        self.assertEqual(1, sum(slot is not None for slot in slots))

    def test_configured_timezone_and_floating_time(self):
        appointment = event('2026-09-11T09:00:00', '2026-09-11T10:00:00')
        self.assertEqual('ffffff', project_day([appointment], date(2026, 9, 11), 'UTC')[7])
        utc = Appointment('', datetime(2026, 9, 11, 9), datetime(2026, 9, 11, 10), '', timezone='UTC')
        self.assertEqual('ffffff', project_day([utc], date(2026, 9, 11))[11])

    def test_invalid_interval_and_separate_default_lists(self):
        with self.assertRaises(ValueError):
            event('2026-09-11T11:00:00', '2026-09-11T10:00:00')
        first, second = Calendar('a', '', ''), Calendar('b', '', '')
        first.appointments.append('sentinel')
        self.assertEqual([], second.appointments)

    def test_person_can_sort_mixed_date_and_datetime_events(self):
        from iot.infrastructure.person import Person
        all_day = Appointment('Urlaub', date(2026, 9, 11), date(2026, 9, 12), '')
        timed = event('2026-09-11T09:00:00+02:00', '2026-09-11T10:00:00+02:00')
        person = Person('Person', [Calendar('Calendar', '', '', [timed, all_day])])
        self.assertEqual([all_day, timed], person.get_n_upcoming_appointments(2))
