import logging
from datetime import datetime
from typing import List

from caldav import CalendarObjectResource
from dateutil.tz import tzlocal
from icalendar.prop import vCategory

from iot.core.configuration import CategoryConfig, CalendarsConfig, CaldavConfig
from iot.infrastructure.time.calendar import Appointment, Calendar


class GlobalCalendarConfig:
    def __init__(self, calendars: List[CaldavConfig], categories: List[CategoryConfig]):
        self.calendars = calendars
        self.categories = categories

    def has_color_for(self, category_name: str) -> bool:
        return any(map(lambda c: c.name.lower() == category_name.lower(), self.categories))

    def get_color_for(self, category_name: str) -> str | None:
        for category in self.categories:
            if category.name.lower() == category_name.lower():
                return category.color_hex
        return None


class CalendarLoader:
    def __init__(self, config: CalendarsConfig):
        self.config = GlobalCalendarConfig(config.calendars, config.categories)
        self.logger = logging.getLogger(self.__class__.__name__)

    def from_caldav_events(self, name: str, url: str, default_color: str,
                           caldav_events: List[CalendarObjectResource]) -> Calendar:
        appointments = []
        for event in caldav_events:
            ical_component = event.icalendar_component
            summary = str(ical_component['SUMMARY'])
            description = str(ical_component['DESCRIPTION']) if 'DESCRIPTION' in ical_component else ''
            start_at = ical_component['DTSTART'].dt
            end_at = ical_component['DTEND'].dt
            color = self.search_color_for_category(default_color, ical_component)
            appointments.append(Appointment(summary, start_at, end_at, color, description))
        return Calendar(name, url, default_color, appointments, last_seen_at=datetime.now(tzlocal()))

    def search_color_for_category(self, default_color: str, ical_component) -> str:
        try:
            if 'CATEGORIES' in ical_component and ical_component['CATEGORIES'] and ical_component['CATEGORIES'].cats:
                categories: vCategory = ical_component['CATEGORIES']
                for category in categories.cats:
                    if self.config.has_color_for(category):
                        return self.config.get_color_for(category)
        except AttributeError as e:
            self.logger.debug('Event had no categories to search color for')
        return default_color
