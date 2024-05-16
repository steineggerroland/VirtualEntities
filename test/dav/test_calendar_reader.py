import unittest
from datetime import datetime
from unittest.mock import Mock

import pytz

from iot.core.configuration import CalendarsConfig, CategoryConfig, CaldavConfig, UrlConf
from iot.dav.calendar_reader import CalendarLoader


class TestCalendarLoader(unittest.TestCase):
    def test_init(self):
        categories = [CategoryConfig("Private", "fff000"), CategoryConfig("Work", "0F0F11")]
        calendars = [CaldavConfig(UrlConf("calendar", "private", "dav.private.url"), "f93E90")]
        calendars_config = CalendarsConfig(categories, calendars)
        calendar_loader = CalendarLoader(calendars_config)
        # then
        self.assertEqual("Private", calendar_loader.config.categories[0].name)
        self.assertEqual("fff000", calendar_loader.config.categories[0].color)
        self.assertEqual("Work", calendar_loader.config.categories[1].name)
        self.assertEqual("0f0f11", calendar_loader.config.categories[1].color)

        self.assertEqual("calendar", calendar_loader.config.calendars[0].application)
        self.assertEqual("private", calendar_loader.config.calendars[0].name)
        self.assertEqual("dav.private.url", calendar_loader.config.calendars[0].url)
        self.assertEqual("f93e90", calendar_loader.config.calendars[0].color)

    def test_has_color_for(self):
        categories = [CategoryConfig("Private", "fff000"), CategoryConfig("Work", "0F0F11")]
        calendars = [CaldavConfig(UrlConf("calendar", "private", "dav.private.url"), "f93E90")]
        calendars_config = CalendarsConfig(categories, calendars)
        calendar_loader = CalendarLoader(calendars_config)
        # then
        self.assertTrue(calendar_loader.config.has_color_for("private"))
        self.assertEqual("fff000", calendar_loader.config.get_color_for("private"))
        self.assertTrue(calendar_loader.config.has_color_for("WoRK"))
        self.assertEqual("0f0f11", calendar_loader.config.get_color_for("WORK"))
        self.assertFalse(calendar_loader.config.has_color_for("special"))
        self.assertFalse(calendar_loader.config.has_color_for("important"))

    def test_from_caldav_events_with_main_data(self):
        calendars_config = CalendarsConfig([], [])
        calendar_loader = CalendarLoader(calendars_config)

        name = "Private"
        url = "private.dav.url"
        color = "ffffff"
        # when
        calendar = calendar_loader.from_caldav_events(name, url, color, [])
        # then
        self.assertEqual(name, calendar.name)
        self.assertEqual(url, calendar.url)
        self.assertEqual(color, calendar.color)

    def test_from_caldav_events(self):
        calendar_loader = CalendarLoader(CalendarsConfig([], []))
        summary = "meeting 93284"
        start_date = datetime.now().astimezone(pytz.timezone("Europe/Berlin"))
        end_date = datetime.now().astimezone(pytz.timezone("Europe/Berlin"))
        icalendar_component = {"SUMMARY": summary, "DTSTART": Mock(dt=start_date), "DTEND": Mock(dt=end_date)}
        dav_object = Mock(icalendar_component=icalendar_component)
        color = "ffffff"
        # when
        calendar = calendar_loader.from_caldav_events("Private", "private.dav.url", color, [dav_object])
        # then
        self.assertEqual(summary, calendar.appointments[0].summary)
        self.assertEqual(start_date, calendar.appointments[0].start_at)
        self.assertEqual(end_date, calendar.appointments[0].end_at)
        self.assertEqual(color, calendar.appointments[0].color)

    def test_from_caldav_events_with_categories(self):
        work_color = "ff0000"
        calendar_loader = CalendarLoader(CalendarsConfig([CategoryConfig("work", work_color)], []))
        summary = "meeting 93284"
        start_date = datetime.now().astimezone(pytz.timezone("Europe/Berlin"))
        end_date = datetime.now().astimezone(pytz.timezone("Europe/Berlin"))
        icalendar_component = {"SUMMARY": summary, "DTSTART": Mock(dt=start_date), "DTEND": Mock(dt=end_date),
                               "CATEGORIES": Mock(cats=["Work", "Meeting"])}
        dav_object = Mock(icalendar_component=icalendar_component)
        # when
        calendar = calendar_loader.from_caldav_events("Private", "private.dav.url", "ffffff", [dav_object])
        # then
        self.assertEqual(summary, calendar.appointments[0].summary)
        self.assertEqual(start_date, calendar.appointments[0].start_at)
        self.assertEqual(end_date, calendar.appointments[0].end_at)
        self.assertEqual(work_color, calendar.appointments[0].color)


if __name__ == '__main__':
    unittest.main()
