import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from unittest.mock import Mock

from iot.core.configuration import VirtualEntityConfig, Sources, CaldavConfig, UrlConf, CalendarsConfig
from iot.infrastructure.person_service import PersonService
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.time.calendar import Calendar
from iot.dav.calendar_reader import CalendarLoader


class CalendarUpdatesTest(unittest.TestCase):
    def test_concurrent_sources_are_preserved_and_failure_clears_on_recovery(self):
        sources = [CaldavConfig(UrlConf('calendar', name, name)) for name in ('a', 'b')]
        service = PersonService(RegisterOfPersons(), VirtualEntityConfig('person', sources=Sources(sources)))
        with ThreadPoolExecutor(2) as pool:
            list(pool.map(lambda name: service.update_calendars([Calendar(name, 'updated', '')]), ('a', 'b')))
        service.mark_calendar_failed('a')
        calendars, errors = service.calendar_snapshot()
        self.assertEqual({'a', 'b'}, {calendar.name for calendar in calendars})
        self.assertTrue(all(calendar.url == 'updated' for calendar in calendars))
        self.assertEqual({'a'}, errors)
        service.update_calendars([Calendar('a', 'recovered', '')])
        self.assertFalse(service.calendar_snapshot()[1])

    def test_all_day_without_end_defaults_to_next_day(self):
        loader = CalendarLoader(CalendarsConfig([], []))
        event = Mock(icalendar_component={'DTSTART': Mock(dt=date(2026, 9, 11))})
        calendar = loader.from_caldav_events('a', '', '', [event])
        self.assertEqual(date(2026, 9, 12), calendar.appointments[0].end_at)

    def test_bad_event_rejects_entire_snapshot(self):
        loader = CalendarLoader(CalendarsConfig([], []))
        with self.assertRaises(ValueError):
            loader.from_caldav_events('a', '', '', [Mock(icalendar_component={})])

    def test_refresh_failure_preserves_previous_calendar(self):
        from unittest.mock import patch
        from iot.dav.calendar_sync import CalendarSync
        source = CaldavConfig(UrlConf('calendar', 'a', 'http://invalid'))
        service = PersonService(RegisterOfPersons(), VirtualEntityConfig('person', sources=Sources([source])))
        original = Calendar('a', 'last-good', '')
        service.update_calendars([original])
        sync = CalendarSync(service, [source], CalendarLoader(CalendarsConfig([], [])))
        with patch('iot.dav.calendar_sync.caldav.DAVClient', side_effect=OSError('offline')):
            with self.assertLogs('iot.dav.calendar_sync', level='ERROR'):
                sync.refresh(source)
        calendars, errors = service.calendar_snapshot()
        self.assertIs(original, calendars[0])
        self.assertEqual({'a'}, errors)

    def test_shutdown_interrupts_scheduled_wait(self):
        from threading import Event
        from iot.dav.calendar_sync import CalendarSync
        source = CaldavConfig(UrlConf('calendar', 'a', '', update_cron='0 0 1 1 *'))
        sync = CalendarSync(Mock(), [source], CalendarLoader(CalendarsConfig([], [])))
        refreshed = Event()
        sync.refresh = lambda source: refreshed.set()
        sync.start()
        self.assertTrue(refreshed.wait(1))
        sync.shutdown()
        self.assertFalse(any(thread.is_alive() for thread in sync._threads))
