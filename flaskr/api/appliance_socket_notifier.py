import logging

from flask_socketio import SocketIO
from python_event_bus import EventBus

from flaskr.api.appliance import ApplianceConverter
from iot.infrastructure.appliance.appliance_events import ApplianceEvents, ApplianceEvent, ApplianceConsumptionEvent, \
    ApplianceRunFinishedEvent
from iot.infrastructure.appliance.appliance_service import ApplianceService


class ApplianceSocketNotifier:
    def __init__(self, socket: SocketIO, appliance_service: ApplianceService, app):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.socket: SocketIO = socket
        self.appliance_service = appliance_service
        self.converter = ApplianceConverter(app)

        @socket.on('connect', namespace='/appliances')
        def handle_celebrate():
            self.logger.debug('client connected')

        specific_events = [ApplianceEvents.CHANGED_CONFIG_NAME, ApplianceEvents.UPDATED_POWER_CONSUMPTION,
                           ApplianceEvents.LOADED, ApplianceEvents.UNLOADED, ApplianceEvents.CLEANED,
                           ApplianceEvents.NOTICED_DIRT]
        for event in filter(lambda e: e not in specific_events, ApplianceEvents):
            EventBus.subscribe(event, self._appliance_updated)
        EventBus.subscribe(ApplianceEvents.UPDATED_POWER_CONSUMPTION,
                           lambda e: self._appliance_power_consumption_updated(e))
        EventBus.subscribe(ApplianceEvents.LOADED, lambda e: self._appliance_updated(e, 'loaded'))
        EventBus.subscribe(ApplianceEvents.UNLOADED, lambda e: self._appliance_updated(e, 'unloaded'))
        EventBus.subscribe(ApplianceEvents.NOTICED_DIRT, lambda e: self._appliance_updated(e, 'noticed_dirt'))
        EventBus.subscribe(ApplianceEvents.CLEANED, lambda e: self._appliance_updated(e, 'cleaned'))
        EventBus.subscribe(ApplianceEvents.FINISHED_RUN, self._finished_run)

        EventBus.subscribe(ApplianceEvents.UNLOADED, self._celebrate)
        EventBus.subscribe(ApplianceEvents.CLEANED, self._celebrate)

    def _appliance_updated(self, event: ApplianceEvent, event_type: str = 'updated'):
        self.socket.emit(f'{event.appliance.name}/{event_type}',
                         {
                             'entity_name': event.appliance.name,
                             'entity': self.converter.convert_appliance_for_frontend_without_context(event.appliance),
                             'event_type': event_type
                         },
                         namespace='/appliances')

    def _finished_run(self, event: ApplianceRunFinishedEvent):
        self.socket.emit(f'{event.appliance.name}/finished_run',
                         {
                             'entity_name': event.appliance.name,
                             'entity': self.converter.convert_appliance_for_frontend_without_context(event.appliance),
                             'event_type': 'finished_run',
                             'run': event.run.to_dict()
                         },
                         namespace='/appliances')

    def _appliance_power_consumption_updated(self, event: ApplianceConsumptionEvent):
        self.socket.emit(f'{event.appliance.name}/power-consumption/updated',
                         {
                             'entity_name': event.appliance.name,
                             'entity': self.converter.convert_appliance_for_frontend_without_context(event.appliance),
                             'event_type': 'power_consumption',
                             'measure': event.measurement.to_dict()
                         },
                         namespace='/appliances')

    def _celebrate(self, _):
        self.socket.emit('celebrate', namespace='/')
