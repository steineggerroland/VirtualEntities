"""CalDAV refresh lifecycle, independent of the MQTT transport."""
import logging
from datetime import datetime, timedelta
from threading import Event, Thread
from zoneinfo import ZoneInfo

import caldav
from croniter import croniter

from iot.core.configuration import CaldavConfig


class CalendarSync:
    def __init__(self, person_service, sources, loader):
        self.person_service = person_service
        self.loader = loader
        self.zone = ZoneInfo(loader.timezone)
        self.logger = logging.getLogger(__name__)
        self._stop = Event()
        self._threads = [Thread(target=self._run, args=(source,), daemon=True)
                         for source in sources if isinstance(source, CaldavConfig)]

    def start(self):
        for thread in self._threads:
            thread.start()

    def shutdown(self, timeout=2):
        self._stop.set()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout)

    def _run(self, source):
        cron = croniter(source.update_cron, datetime.now(self.zone))
        while not self._stop.is_set():
            self.refresh(source)
            delay = (cron.get_next(datetime) - datetime.now(self.zone)).total_seconds()
            if self._stop.wait(max(0, delay)):
                return

    def refresh(self, source):
        try:
            day = datetime.now(self.zone).date()
            start = datetime.combine(day, datetime.min.time(), self.zone)
            end = datetime.combine(day + timedelta(days=7), datetime.min.time(), self.zone)
            credentials = ({'username': source.username, 'password': source.password}
                           if source.has_credentials() else {})
            with caldav.DAVClient(url=source.url, timeout=10, **credentials) as client:
                events = client.calendar(url=source.url).search(start=start, end=end, event=True, expand=True)
                calendar = self.loader.from_caldav_events(source.name, source.url, source.color_hex, events)
                calendar.loaded_from, calendar.loaded_until = day, day + timedelta(days=7)
                self.person_service.update_calendars([calendar])
        except Exception:
            self.person_service.mark_calendar_failed(source.name)
            self.logger.exception('Calendar refresh failed for %s', source.name)
