from python_event_bus import EventBus

from iot.core.configuration import Sources, Destinations
from iot.infrastructure.appliance.appliance_events import ApplianceEvents
from iot.infrastructure.appliance.appliance_service import ApplianceService, DatabaseException
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator


class MqttApplianceMediator(MqttMediator):
    def __init__(self, appliance_service: ApplianceService, mqtt_client: MqttClient):
        super().__init__(mqtt_client)
        self.appliance_service = appliance_service
        self.sources = {}
        self.destinations = {}
        EventBus.subscribe(ApplianceEvents.CHANGED_CONFIG_NAME, self.rename)

    def add_appliance_by_config(self, appliance_name: str, mqtt_sources: Sources | None = None,
                                destinations: Destinations | None = None):
        if appliance_name in self.sources or appliance_name in self.destinations:
            raise RuntimeError()
        self.sources[appliance_name] = mqtt_sources
        self.destinations[appliance_name] = destinations
        self._process_sources_for(appliance_name, mqtt_sources)
        self._process_destinations_for(appliance_name, destinations)

    def _process_destinations_for(self, appliance_name: str, destinations: Destinations):
        self.handle_destinations(destinations.planned_notifications if destinations else [],
                                 lambda: self.appliance_service.get_appliance(appliance_name).to_dict())

    def _process_sources_for(self, appliance_name: str, mqtt_sources: Sources):
        for source in mqtt_sources.list if mqtt_sources else []:
            if source.measures[0].type == 'consumption':
                if source.measures[0].path:
                    json_path = str(source.measures[0].path)
                    self.mqtt_client.subscribe(appliance_name, source.mqtt_topic,
                                               lambda msg: self.power_consumption_update(appliance_name, msg,
                                                                                         json_path))
                else:
                    self.mqtt_client.subscribe(appliance_name, source.mqtt_topic,
                                               lambda msg: self.power_consumption_update(appliance_name, msg))
            if source.measures[0].type == 'loading':
                self.mqtt_client.subscribe(appliance_name, source.mqtt_topic,
                                           lambda msg: self.load_appliance(appliance_name, msg))
            if source.measures[0].type == 'unloading':
                self.mqtt_client.subscribe(appliance_name, source.mqtt_topic,
                                           lambda msg: self.unload_appliance(appliance_name, msg))

    def power_consumption_update(self, appliance_name: str, msg, json_path=None):
        try:
            consumption = self._read_value_from_message(msg, json_path, float)
            self.appliance_service.update_power_consumption(appliance_name, consumption)
            self.logger.debug("Updated power consumption '%s'", consumption)
        except DatabaseException as e:
            self.logger.error("Failed to update appliance's %s power consumption because of database error '%s'",
                              appliance_name, e, exc_info=True)

    def load_appliance(self, appliance_name, msg=None):
        try:
            needs_unloading = self._read_value_from_message(msg, value_type=bool) if msg.payload else True
            self.appliance_service.loaded(appliance_name, needs_unloading=needs_unloading)
            self.logger.debug("Set appliance loaded.")
        except DatabaseException as e:
            self.logger.error("Failed set appliance %s loaded because of database error '%s'",
                              appliance_name, e, exc_info=True)

    def unload_appliance(self, appliance_name, msg=None):
        try:
            self.appliance_service.unloaded(appliance_name)
            self.logger.debug("Set appliance unloaded.")
        except DatabaseException as e:
            self.logger.error("Failed set appliance %s unloaded because of database error '%s'",
                              appliance_name, e, exc_info=True)

    def rename(self, name: str, old_name: str):
        self.mqtt_client.unsubscribe(old_name)
        if old_name in self.sources:
            self._process_sources_for(name, self.sources[old_name])
            self.sources[name] = self.sources[old_name]
            del self.sources[old_name]
        if old_name in self.destinations:
            self._process_destinations_for(name, self.destinations[old_name])
            self.destinations[name] = self.destinations[old_name]
            del self.destinations[old_name]
