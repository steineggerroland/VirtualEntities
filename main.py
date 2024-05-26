import logging
import sys
from pathlib import Path
from time import sleep

from flaskr import create_app
from iot.core.configuration import load_configuration
from iot.core.storage import Storage
from iot.dav.calendar_reader import CalendarLoader
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.machine.machine_service import MachineService, \
    supports_thing_type as machine_service_supports_thing_type
from iot.infrastructure.person_service import PersonService, supports_thing_type as person_service_supports_thing_type
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.room_catalog import RoomCatalog
from iot.infrastructure.room_service import RoomService, supports_thing_type as room_service_supports_thing_type
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_machine_mediator import MqttMachineMediator
from iot.mqtt.mqtt_person_mediator import MqttPersonMediator
from iot.mqtt.mqtt_room_mediator import MqttRoomMediator

DEFAULT_FLASK_CONFIG_FILE_NAME = "default_flask.yaml"
DB_JSON_FILE = 'data/db.json'
CONFIG_FILE_NAME = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'


def run():
    logger = logging.getLogger("main")
    logger.debug("Starting")
    config = load_configuration(CONFIG_FILE_NAME)
    logger.debug("Configuration loaded")
    client = MqttClient(config.mqtt)
    logger.debug("Mqtt client loaded")
    storage = Storage(Path(DB_JSON_FILE), [thing.name for thing in config.things], config.time_series)
    appliance_depot = ApplianceDepot(storage)
    room_catalog = RoomCatalog(storage)
    register_of_persons = RegisterOfPersons()
    logger.debug("Storage loaded")
    mqtt_mediators = []
    for thing_config in config.things:
        if machine_service_supports_thing_type(thing_type=thing_config.type):
            machine_service = MachineService(appliance_depot, thing_config)
            logger.debug("Machine service for '%s' loaded" % thing_config.name)
            mqtt_mediators.append(
                MqttMachineMediator(machine_service, thing_config.sources, thing_config.destinations, client))
            logger.debug("Mqtt machine mediator for '%s' loaded" % thing_config.name)
        elif room_service_supports_thing_type(thing_type=thing_config.type):
            room_service = RoomService(room_catalog, storage, thing_config)
            logger.debug("Room service for '%s' loaded" % thing_config.name)
            mqtt_mediators.append(
                MqttRoomMediator(client, room_service, thing_config))
            logger.debug("Mqtt room mediator for '%s' loaded" % thing_config.name)
        elif person_service_supports_thing_type(thing_type=thing_config.type):
            person_service = PersonService(register_of_persons, thing_config)
            logger.debug("Person service for '%s' loaded" % thing_config.name)
            mqtt_mediators.append(
                MqttPersonMediator(client, person_service, thing_config, CalendarLoader(config.calendars_config)))
            logger.debug("Mqtt person mediator for '%s' loaded" % thing_config.name)
        else:
            logger.error('Unsupported thing of type %s' % thing_config.type)

    try:
        storage.start()
        client.start()
        for mqtt_mediator in mqtt_mediators:
            mqtt_mediator.start()

        frontend = create_app(Path(__file__).parent.absolute().joinpath(DEFAULT_FLASK_CONFIG_FILE_NAME).as_posix(),
                              config.flaskr)
        frontend.run()
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
