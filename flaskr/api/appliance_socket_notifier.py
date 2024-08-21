import logging

from flask_socketio import SocketIO
from python_event_bus import EventBus

from iot.infrastructure.appliance.appliance_events import ApplianceEvents, ApplianceEvent, ApplianceConsumptionEvent
from iot.infrastructure.appliance.appliance_service import ApplianceService


class ApplianceSocketNotifier:
    def __init__(self, socket: SocketIO, appliance_service: ApplianceService):
        self.socket: SocketIO = socket
        self.appliance_service = appliance_service
        self.logger = logging.getLogger(self.__class__.__qualname__)

        @socket.on('connect', namespace='/appliances')
        def handle_celebrate():
            self.logger.debug('client connected')

        specific_events = [ApplianceEvents.CHANGED_CONFIG_NAME, ApplianceEvents.UPDATED_POWER_CONSUMPTION]
        for event in filter(lambda e: e not in specific_events, ApplianceEvents):
            EventBus.subscribe(event, self._appliance_updated)
        EventBus.subscribe(ApplianceEvents.UPDATED_POWER_CONSUMPTION, self._appliance_power_consumption_updated)

        EventBus.subscribe(ApplianceEvents.UNLOADED, self._celebrate)
        EventBus.subscribe(ApplianceEvents.CLEANED, self._celebrate)

    def _appliance_updated(self, event: ApplianceEvent):
        self.socket.emit(f'{event.appliance.name}/updated', {'appliance': event.appliance.to_dict()},
                         namespace='/appliances')

    def _appliance_power_consumption_updated(self, event: ApplianceConsumptionEvent):
        self.socket.emit(f'{event.appliance.name}/power-consumption/updated',
                         {'appliance': event.appliance.to_dict(), 'measure': event.measurement.to_dict()},
                         namespace='/appliances'
                         )

    def _celebrate(self, _):
        self.socket.emit('celebrate', namespace='/')
