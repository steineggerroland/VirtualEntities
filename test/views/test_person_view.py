import unittest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

import pytz

from flaskr.views.Person import Details, preview_days
from iot.infrastructure.person import Person
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.time.calendar import Calendar


class PersonPreviewTest(unittest.TestCase):
    def test_details_renders_calendar_preview_without_passing_dates_as_timestamps(self):
        register = RegisterOfPersons()
        register.enlist(Person('Example', [Calendar('Personal', 'https://calendar.example.test', 'ffffff')]))

        with patch('flaskr.views.Person.render_template', return_value='rendered') as render_template:
            result = Details(register).dispatch_request('Example')

        self.assertEqual('rendered', result)
        preview = render_template.call_args.kwargs['days_to_appointments']
        self.assertEqual(7, len(preview))
        self.assertIsInstance(preview[0][2], datetime)
        self.assertIsNotNone(preview[0][2].tzinfo)

    def test_uses_timezone_aware_day_boundaries_for_each_preview_day(self):
        person = Mock()
        timezone = pytz.timezone('Europe/Berlin')

        days = preview_days(person, date(2026, 9, 11), timezone)

        self.assertEqual(7, len(days))
        self.assertEqual(date(2026, 9, 11), days[0][0])
        self.assertEqual(date(2026, 9, 17), days[-1][0])
        first_start = days[0][2]
        self.assertEqual(timezone.localize(datetime(2026, 9, 11)), first_start)
        self.assertEqual(first_start + timedelta(days=1), days[0][3])
        self.assertEqual(first_start, person.get_appointments_for.call_args_list[0].args[0])
        self.assertEqual(timedelta(days=1), person.get_appointments_for.call_args_list[0].args[1])


if __name__ == '__main__':
    unittest.main()
