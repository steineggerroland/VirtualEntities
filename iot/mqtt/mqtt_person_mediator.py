from datetime import datetime, timedelta

from zoneinfo import ZoneInfo
from iot.dav.calendar_sync import CalendarSync

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
        self.calendar_loader = calendar_loader
        self.calendar_sync = CalendarSync(person_service, config.sources.list, calendar_loader)

        self.has_daily_appointment_notification = any(
            filter(lambda dest: dest.subject == DAILY_APPOINTMENTS, config.destinations.planned_notifications))

        self.handle_destinations(
            list(
                filter(lambda dest: dest.subject == DAILY_APPOINTMENTS, config.destinations.planned_notifications)),
            lambda: self._get_appointments_for_today())


    def _get_appointments_for_today(self):
        zone = ZoneInfo(self.calendar_loader.timezone)
        day = datetime.now(zone).date()
        start = datetime.combine(day, datetime.min.time(), zone)
        end = datetime.combine(day + timedelta(days=1), datetime.min.time(), zone)
        return {"appointments": [appointment.to_dict() for appointment in
                                 self.person_service.get_person().get_appointments_for(start, end - start)
                                 if not appointment.is_all_day]}

    def start(self):
        super().start()
        self.calendar_sync.start()

    def shutdown(self, timeout=2):
        self.calendar_sync.shutdown(timeout)
        super().shutdown(timeout)
