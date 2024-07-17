import time
from datetime import datetime, timedelta
from threading import Thread
from typing import List

import caldav
from croniter import croniter
from dateutil.tz import tzlocal

from iot.core.configuration import VirtualEntityConfig, CaldavConfig
from iot.dav.calendar_reader import CalendarLoader
from iot.infrastructure.person_service import PersonService
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator

DAILY_APPOINTMENTS = "daily-appointments"


class MqttPersonMediator(MqttMediator):
    def __init__(self, mqtt_client: MqttClient, person_service: PersonService, config: VirtualEntityConfig,
                 calendar_loader: CalendarLoader):
        super().__init__(mqtt_client)
        self.person_service = person_service
        self.scheduled_caldav_download_threads = []
        self.calendar_loader = calendar_loader

        self.has_daily_appointment_notification = any(
            filter(lambda dest: dest.subject == DAILY_APPOINTMENTS, config.destinations.planned_notifications))

        self.handle_destinations(
            list(
                filter(lambda dest: dest.subject == DAILY_APPOINTMENTS, config.destinations.planned_notifications)),
            lambda: self._get_appointments_for_today())
        self._handle_calendar_sources(filter(lambda source: type(source) is CaldavConfig, config.sources.list))

    def _get_appointments_for_today(self):
        start_of_today = datetime.combine(datetime.now(tzlocal()), datetime.min.time())
        return {"appointments": list(map(lambda appointment: appointment.to_dict(),
                                         self.person_service.get_person().get_appointments_for(start_of_today,
                                                                                               timedelta(hours=23,
                                                                                                         minutes=59,
                                                                                                         seconds=59))))}

    def _handle_calendar_sources(self, sources: List[CaldavConfig]):
        for calendar_source in sources:
            thread = Thread(target=self._scheduled_caldav_download, args=[calendar_source])
            thread.daemon = True
            self.scheduled_update_threads.append(thread)

    def _scheduled_caldav_download(self, calendar_source: CaldavConfig):
        cron = croniter(calendar_source.update_cron, datetime.now(tzlocal()))
        while True:
            self._update_calendars_from_caldav(calendar_source)
            delta = cron.get_next(datetime) - datetime.now(tzlocal())
            time.sleep(max(0, delta.total_seconds()))

    def _update_calendars_from_caldav(self, calendar_source: CaldavConfig):
        try:
            with (caldav.DAVClient(
                    url=calendar_source.url,
                    username=calendar_source.username,
                    password=calendar_source.password) if calendar_source.has_credentials()
                  else caldav.DAVClient(url=calendar_source.url)
                  as client):
                # load the next 7 days which are needed for the website
                start = datetime.combine(datetime.now(tzlocal()), datetime.min.time())
                end = datetime.combine(datetime.now(tzlocal()) + timedelta(days=6), datetime.max.time())
                caldav_calendar = client.calendar(url=calendar_source.url)
                relevant_events = caldav_calendar.search(start=start,
                                                         end=end,
                                                         event=True, expand=True)
                updated_calendar = self.calendar_loader.from_caldav_events(calendar_source.name, calendar_source.url,
                                                                           calendar_source.color_hex, relevant_events)
                self.person_service.update_calendars([updated_calendar])
                self.logger.debug(
                    "Updated calendar '%s' with %s appointments of person %s from %s", caldav_calendar.name,
                    len(relevant_events), self.person_service.get_person().name, calendar_source.url)
        except Exception as e:
            self.logger.error("Failed to update calendars from source %s with error", calendar_source.url, exc_info=e)

    def start(self):
        super().start()
        for thread in self.scheduled_caldav_download_threads:
            if not thread.is_alive():
                thread.start()

    def shutdown(self, timeout=2):
        super().shutdown(timeout)
        for thread in self.scheduled_caldav_download_threads:
            if not thread.is_alive():
                thread.join(timeout)
