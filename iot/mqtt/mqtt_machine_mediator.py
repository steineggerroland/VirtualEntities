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
            if source.type == 'consumption':
                mqtt_client.subscribe(source.topic, lambda msg: self.power_consumption_update(msg, source.path))
            if source.type == 'loading':
                mqtt_client.subscribe(source.topic, self.load_machine)
            if source.type == 'unloading':
                mqtt_client.subscribe(source.topic, self.unload_machine)

        self.handle_destinations(destinations, lambda: self.machine_service.thing.to_dict())

    def power_consumption_update(self, msg, json_path=None):
        try:
            consumption = self._read_value_from_message(msg, json_path)
            self.machine_service.update_power_consumption(consumption)
            self.logger.debug("Updated power consumption '%s'", consumption)
        except DatabaseException as e:
            self.logger.error("Failed update power consumption '%s' because of database error.", msg.topic, exc_info=e)

    def load_machine(self, msg):
        try:
            self.machine_service.loaded()
            self.logger.debug("Set machine loaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine loaded because of database error.", msg.topic, exc_info=e)

    def unload_machine(self, msg):
        try:
            self.machine_service.unloaded()
            self.logger.debug("Set machine unloaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine unloaded because of database error.", msg.topic, exc_info=e)
