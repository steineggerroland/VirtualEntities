import logging
import sys
from time import sleep

from iot.core.configuration import load_configuration
from iot.core.storage import Storage
from iot.infrastructure.machine.machine_service import MachineService
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_machine_mediator import MqttMachineMediator

DB_JSON_FILE = 'data/db.json'
CONFIG_FILE_NAME = sys.argv[1] if len(sys.argv) >= 1 else 'config.yaml'


def run():
    logger = logging.getLogger("main")
    logger.debug("Starting")
    config = load_configuration(CONFIG_FILE_NAME)
    logger.debug("Configuration loaded")
    storage = Storage(DB_JSON_FILE, [thing.name for thing in config.things])
    logger.debug("Storage loaded")
    client = MqttClient(config.mqtt)
    logger.debug("Mqtt client loaded")
    mqtt_mediators = []
    for thing_config in config.things:
        machine_service = MachineService(storage, thing_config)
        logger.debug("Service for '%s' loaded" % thing_config.name)
        mqtt_mediators.append(
            MqttMachineMediator(machine_service, thing_config.sources, thing_config.destinations, client))
        logger.debug("Mqtt mediator for '%s' loaded" % thing_config.name)

    try:
        client.start()
        for mqtt_mediator in mqtt_mediators:
            mqtt_mediator.start()
        logger.info("Started.")
        while True:
            sleep(10)
    except KeyboardInterrupt:
        logger.info("Shutting down.")
    finally:
        storage.shutdown()
        client.stop()


if __name__ == '__main__':
    logging.basicConfig(filename='data/default.log', encoding='utf-8',
                        level=logging.DEBUG if sys.flags.debug else logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    run()
