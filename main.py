import logging
import sys
from pathlib import Path
from time import sleep
from typing import List

from flaskr import create_app
from iot.core.configuration import VirtualEntityConfig
from iot.core.configuration_manager import ConfigurationManager
from iot.core.storage import Storage
from iot.core.time_series_storage import TimeSeriesStorage
from iot.dav.calendar_reader import CalendarLoader
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.machine.machine_service import MachineService, \
    supports_entity_type as machine_service_supports_entity_type
from iot.infrastructure.person_service import PersonService, supports_entity_type as person_service_supports_entity_type
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.room_catalog import RoomCatalog
from iot.infrastructure.room_service import RoomService, supports_entity_type as room_service_supports_entity_type
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_machine_mediator import MqttMachineMediator
from iot.mqtt.mqtt_person_mediator import MqttPersonMediator
from iot.mqtt.mqtt_room_mediator import MqttRoomMediator

DEFAULT_FLASK_CONFIG_FILE_NAME = "default_flask.yaml"
DB_JSON_FILE = sys.argv[2] if len(sys.argv) > 2 else 'data/db.json'
CONFIG_FILE_NAME = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
LOG_FILE_NAME = sys.argv[3] if len(sys.argv) > 3 else 'data/default.log'


def run():
    logger = logging.getLogger("main")
    logger.debug("Starting")
    config_manager = ConfigurationManager()
    config = config_manager.load(CONFIG_FILE_NAME)
    logger.debug("Configuration loaded")
    client = MqttClient(config.mqtt)
    logger.debug("Mqtt client loaded")
    storage = Storage(Path(DB_JSON_FILE), [entity.name for entity in config.entities])
    time_series_storage = TimeSeriesStorage(config.time_series)
    appliance_depot = ApplianceDepot(storage, time_series_storage)
    room_catalog = RoomCatalog(storage)
    register_of_persons = RegisterOfPersons()
    logger.debug("Storage loaded")
    machine_configs: List[VirtualEntityConfig] = list(
        filter(lambda t: machine_service_supports_entity_type(entity_type=t.type), config.entities))
    machine_service = MachineService(appliance_depot, time_series_storage, config_manager)
    machine_service.add_machines_by_config(machine_configs)
    mqtt_mediators = []
    logger.debug("Machine service for loaded")
    mqtt_machine_mediator = MqttMachineMediator(machine_service, client)
    mqtt_mediators.append(mqtt_machine_mediator)
    for entity_config in machine_configs:
        mqtt_machine_mediator.add_machine_by_config(entity_config.name, entity_config.sources,
                                                    entity_config.destinations)
    logger.debug("Mqtt machine mediator loaded")
    for entity_config in config.entities:
        if room_service_supports_entity_type(entity_type=entity_config.type):
            room_service = RoomService(room_catalog, time_series_storage, entity_config)
            logger.debug("Room service for '%s' loaded" % entity_config.name)
            mqtt_mediators.append(
                MqttRoomMediator(client, room_service, entity_config))
            logger.debug("Mqtt room mediator for '%s' loaded" % entity_config.name)
        elif person_service_supports_entity_type(entity_type=entity_config.type):
            person_service = PersonService(register_of_persons, entity_config)
            logger.debug("Person service for '%s' loaded" % entity_config.name)
            mqtt_mediators.append(
                MqttPersonMediator(client, person_service, entity_config, CalendarLoader(config.calendars_config)))
            logger.debug("Mqtt person mediator for '%s' loaded" % entity_config.name)
        elif not machine_service_supports_entity_type(entity_type=entity_config.type):
            logger.error('Unsupported entity of type %s' % entity_config.type)

    try:
        storage.start()
        client.start()
        for mqtt_mediator in mqtt_mediators:
            mqtt_mediator.start()

        frontend = create_app(Path(__file__).parent.absolute().joinpath(DEFAULT_FLASK_CONFIG_FILE_NAME).as_posix(),
                              machine_service, appliance_depot, time_series_storage, room_catalog, register_of_persons,
                              config_manager, config.flaskr)
        frontend.run(host=config.flaskr['HOST'] if 'HOST' in config.flaskr else None,
                     port=config.flaskr['PORT'] if 'PORT' in config.flaskr else None)
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
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG if sys.flags.debug else logging.INFO,
                        format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s',
                        handlers=[stdout_handler, logging.FileHandler(filename=LOG_FILE_NAME, encoding='utf-8')])
    run()
