from iot.core.configuration import Sources, Destinations
from iot.infrastructure.machine.machine_service import MachineService, DatabaseException
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator


class MqttMachineMediator(MqttMediator):
    def __init__(self, machine_service: MachineService, mqtt_sources: Sources, destinations: Destinations,
                 mqtt_client: MqttClient):
        super().__init__(mqtt_client)
        self.machine_service = machine_service

        for source in mqtt_sources.list:
            if source.measures[0].type == 'consumption':
                if source.measures[0].path:
                    json_path = str(source.measures[0].path)
                    mqtt_client.subscribe(source.topic, lambda msg: self.power_consumption_update(msg, json_path))
                else:
                    mqtt_client.subscribe(source.topic, lambda msg: self.power_consumption_update(msg))
            if source.measures[0].type == 'loading':
                mqtt_client.subscribe(source.topic, self.load_machine)
            if source.measures[0].type == 'unloading':
                mqtt_client.subscribe(source.topic, lambda msg: self.unload_machine())

        self.handle_destinations(destinations.planned_notifications if destinations else [],
                                 lambda: self.machine_service.get_machine().to_dict())

    def power_consumption_update(self, msg, json_path=None):
        try:
            consumption = self._read_value_from_message(msg, json_path, float)
            self.machine_service.update_power_consumption(consumption)
            self.logger.debug("Updated power consumption '%s'", consumption)
        except DatabaseException as e:
            self.logger.error("Failed to update machine's %s power consumption because of database error '%s'",
                              self.machine_service.get_machine().name, e, exc_info=True)

    def load_machine(self, msg):
        try:
            needs_unloading = self._read_value_from_message(msg, value_type=bool) if msg.payload else True
            self.machine_service.loaded(needs_unloading=needs_unloading)
            self.logger.debug("Set machine loaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine %s loaded because of database error '%s'",
                              self.machine_service.get_machine().name, e, exc_info=True)

    def unload_machine(self):
        try:
            self.machine_service.unloaded()
            self.logger.debug("Set machine unloaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine %s unloaded because of database error '%s'",
                              self.machine_service.get_machine().name, e, exc_info=True)
