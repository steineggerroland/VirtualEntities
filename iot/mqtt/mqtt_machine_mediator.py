from python_event_bus import EventBus

from iot.core.configuration import Sources, Destinations
from iot.infrastructure.machine.machine_service import MachineService, DatabaseException
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator


class MqttMachineMediator(MqttMediator):
    def __init__(self, machine_service: MachineService, mqtt_client: MqttClient):
        super().__init__(mqtt_client)
        self.machine_service = machine_service
        self.sources = {}
        self.destinations = {}
        EventBus.subscribe("entity_configs/changed_config_name", self.rename)

    def add_machine_by_config(self, machine_name: str, mqtt_sources: Sources | None = None,
                              destinations: Destinations | None = None):
        if machine_name in self.sources or machine_name in self.destinations:
            raise RuntimeError()
        self.sources[machine_name] = mqtt_sources
        self.destinations[machine_name] = destinations
        self._process_sources_for(machine_name, mqtt_sources)
        self._process_destinations_for(machine_name, destinations)

    def _process_destinations_for(self, machine_name: str, destinations: Destinations):
        self.handle_destinations(destinations.planned_notifications if destinations else [],
                                 lambda: self.machine_service.get_machine(machine_name).to_dict())

    def _process_sources_for(self, machine_name: str, mqtt_sources: Sources):
        for source in mqtt_sources.list if mqtt_sources else []:
            if source.measures[0].type == 'consumption':
                if source.measures[0].path:
                    json_path = str(source.measures[0].path)
                    self.mqtt_client.subscribe(machine_name, source.mqtt_topic,
                                               lambda msg: self.power_consumption_update(machine_name, msg, json_path))
                else:
                    self.mqtt_client.subscribe(machine_name, source.mqtt_topic,
                                               lambda msg: self.power_consumption_update(machine_name, msg))
            if source.measures[0].type == 'loading':
                self.mqtt_client.subscribe(machine_name, source.mqtt_topic,
                                           lambda msg: self.load_machine(machine_name, msg))
            if source.measures[0].type == 'unloading':
                self.mqtt_client.subscribe(machine_name, source.mqtt_topic,
                                           lambda msg: self.unload_machine(machine_name, msg))

    def power_consumption_update(self, machine_name: str, msg, json_path=None):
        try:
            consumption = self._read_value_from_message(msg, json_path, float)
            self.machine_service.update_power_consumption(machine_name, consumption)
            self.logger.debug("Updated power consumption '%s'", consumption)
        except DatabaseException as e:
            self.logger.error("Failed to update machine's %s power consumption because of database error '%s'",
                              machine_name, e, exc_info=True)

    def load_machine(self, machine_name, msg=None):
        try:
            needs_unloading = self._read_value_from_message(msg, value_type=bool) if msg.payload else True
            self.machine_service.loaded(machine_name, needs_unloading=needs_unloading)
            self.logger.debug("Set machine loaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine %s loaded because of database error '%s'",
                              machine_name, e, exc_info=True)

    def unload_machine(self, machine_name, msg=None):
        try:
            self.machine_service.unloaded(machine_name)
            self.logger.debug("Set machine unloaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine %s unloaded because of database error '%s'",
                              machine_name, e, exc_info=True)

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
