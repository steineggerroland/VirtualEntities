import logging
import sys
from pathlib import Path
from time import sleep

from iot.core.configuration import load_configuration
from iot.core.storage import Storage
from iot.infrastructure.machine.machine_service import MachineService, \
    supports_thing_type as machine_service_supports_thing_type
from iot.infrastructure.room_service import RoomService, supports_thing_type as room_service_supports_thing_type
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_machine_mediator import MqttMachineMediator
from iot.mqtt.mqtt_room_mediator import MqttRoomMediator

DB_JSON_FILE = 'data/db.json'
CONFIG_FILE_NAME = sys.argv[1] if len(sys.argv) >= 1 else 'config.yaml'


def run():
    logger = logging.getLogger("main")
    logger.debug("Starting")
    config = load_configuration(CONFIG_FILE_NAME)
    logger.debug("Configuration loaded")
    storage = Storage(Path(DB_JSON_FILE), [thing.name for thing in config.things], config.time_series)
    logger.debug("Storage loaded")
    client = MqttClient(config.mqtt)
    logger.debug("Mqtt client loaded")
    mqtt_mediators = []
    for thing_config in config.things:
        if machine_service_supports_thing_type(thing_type=thing_config.type):
            machine_service = MachineService(storage, thing_config)
            logger.debug("Machine service for '%s' loaded" % thing_config.name)
            mqtt_mediators.append(
                MqttMachineMediator(machine_service, thing_config.sources, thing_config.destinations, client))
            logger.debug("Mqtt machine mediator for '%s' loaded" % thing_config.name)
        elif room_service_supports_thing_type(thing_type=thing_config.type):
            machine_service = RoomService(storage, thing_config)
            logger.debug("Room service for '%s' loaded" % thing_config.name)
            mqtt_mediators.append(
                MqttRoomMediator(client, machine_service, thing_config))
            logger.debug("Mqtt room mediator for '%s' loaded" % thing_config.name)
        else:
            logger.error('Unsupported thing of type %s' % thing_config.type)

    try:
        storage.start()
        client.start()
        for mqtt_mediator in mqtt_mediators:
            mqtt_mediator.start()
        logger.info("Started.")
        while True:
            sleep(10)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down.")
    finally:
        for mqtt_mediator in mqtt_mediators:
            mqtt_mediator.shutdown()
        storage.shutdown()
        client.stop()


if __name__ == '__main__':
    logging.basicConfig(filename='data/default.log', encoding='utf-8',
                        level=logging.DEBUG if sys.flags.debug else logging.INFO,
                        format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s')
    run()
