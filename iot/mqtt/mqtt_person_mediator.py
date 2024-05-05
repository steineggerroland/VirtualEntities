from iot.infrastructure.person_service import PersonService
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator


class MqttPersonMediator(MqttMediator):
    def __init__(self, mqtt_client: MqttClient, person_service: PersonService):
        super().__init__(mqtt_client)
        self.person_service = person_service
        raise NotImplemented()
