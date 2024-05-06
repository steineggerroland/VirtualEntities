import sys
import time
from datetime import datetime, timedelta
from functools import reduce
from threading import Thread
from typing import List

import caldav
from croniter import croniter

from iot.core.configuration import IotThingConfig, UrlConf
from iot.infrastructure.person_service import PersonService
from iot.infrastructure.time.calendar import Calendar
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator


class MqttPersonMediator(MqttMediator):
    def __init__(self, mqtt_client: MqttClient, person_service: PersonService, config: IotThingConfig):
        super().__init__(mqtt_client)
        self.person_service = person_service
        self.scheduled_caldav_download_threads = []
        self._handle_calendar_sources(filter(lambda source: type(source) is UrlConf and
                                                            source.application == "calendar", config.sources.list))

    def _handle_calendar_sources(self, sources: List[UrlConf]):
        for calendar_source in sources:
            thread = Thread(target=self._scheduled_caldav_download, args=[calendar_source])
            thread.daemon = True
            self.scheduled_update_threads.append(thread)

    def _scheduled_caldav_download(self, calendar_source: UrlConf):
        cron = croniter(calendar_source.update_cron, datetime.now())
        while True:
            delta = cron.get_next(datetime) - datetime.now()
            time.sleep(max(0, delta.total_seconds()))
            self._update_calendars_from_caldav(calendar_source)
            sys.exit()

    def _update_calendars_from_caldav(self, calendar_source):
        try:
            with (caldav.DAVClient(
                    url=calendar_source.url,
                    username=calendar_source.username,
                    password=calendar_source.password) if calendar_source.username
                  else caldav.DAVClient(url=calendar_source.url)
                  as client):
                principal = client.principal()
                updated_calendars = list(
                    map(lambda caldav_cal: Calendar.from_caldav(caldav_cal),
                        principal.calendars()))
                self.person_service.update_calendars(updated_calendars)
                self.logger.debug(
                    "Updated %s calendars with %s appointments of person %s from %s", len(updated_calendars),
                    reduce(lambda a, b: a + b, map(lambda cal: len(cal.appointments), updated_calendars), 0),
                    self.person_service.person.name, calendar_source.url)
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
