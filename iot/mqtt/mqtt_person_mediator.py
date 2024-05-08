import time
from datetime import datetime, timedelta
from threading import Thread
from typing import List

import caldav
from croniter import croniter

from iot.core.configuration import IotThingConfig, UrlConf
from iot.infrastructure.person_service import PersonService
from iot.infrastructure.time.calendar import Calendar
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator

DAILY_APPOINTMENTS = "daily-appointments"


class MqttPersonMediator(MqttMediator):
    def __init__(self, mqtt_client: MqttClient, person_service: PersonService, config: IotThingConfig):
        super().__init__(mqtt_client)
        self.person_service = person_service
        self.scheduled_caldav_download_threads = []

        self.has_daily_appointment_notification = any(
            filter(lambda dest: dest.subject == DAILY_APPOINTMENTS, config.destinations.planned_notifications))

        self.handle_destinations(
            list(
                filter(lambda dest: dest.subject == DAILY_APPOINTMENTS, config.destinations.planned_notifications)),
            lambda: self._get_appointments_for_today())
        self._handle_calendar_sources(filter(lambda source: type(source) is UrlConf and
                                                            source.application == "calendar", config.sources.list))

    def _get_appointments_for_today(self):
        start_of_today = datetime.combine(datetime.now(), datetime.min.time())
        return {"appointments": list(map(lambda appointment: appointment.to_dict(),
                                         self.person_service.person.get_appointments_for(start_of_today,
                                                                                         timedelta(hours=23, minutes=59,
                                                                                                   seconds=59))))}

    def _handle_calendar_sources(self, sources: List[UrlConf]):
        for calendar_source in sources:
            thread = Thread(target=self._scheduled_caldav_download, args=[calendar_source])
            thread.daemon = True
            self.scheduled_update_threads.append(thread)

    def _scheduled_caldav_download(self, calendar_source: UrlConf):
        cron = croniter(calendar_source.update_cron, datetime.now())
        while True:
            self._update_calendars_from_caldav(calendar_source)
            delta = cron.get_next(datetime) - datetime.now()
            time.sleep(max(0, delta.total_seconds()))

    def _update_calendars_from_caldav(self, calendar_source: UrlConf):
        try:
            with (caldav.DAVClient(
                    url=calendar_source.url,
                    username=calendar_source.username,
                    password=calendar_source.password) if calendar_source.has_credentials()
                  else caldav.DAVClient(url=calendar_source.url)
                  as client):
                if self.has_daily_appointment_notification:
                    start = datetime.combine(datetime.now(), datetime.min.time())
                    end = datetime.combine(datetime.now(), datetime.max.time())
                else:
                    self.logger.debug("There are no planned updates for the calendar, therefore, no data is requested")
                    return
                caldav_calendar = client.calendar(url=calendar_source.url)
                relevant_events = caldav_calendar.search(start=start,
                                                         end=end,
                                                         event=True, expand=True)
                updated_calendar = Calendar.from_caldav_events(caldav_calendar.name, relevant_events)
                self.person_service.update_calendars([updated_calendar])
                self.logger.debug(
                    "Updated calendar '%s' with %s appointments of person %s from %s", caldav_calendar.name,
                    len(relevant_events), self.person_service.person.name, calendar_source.url)
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
