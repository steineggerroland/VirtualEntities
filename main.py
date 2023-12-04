import logging
import sys
from time import sleep

from iot.core.Storage import Storage
from iot.core.configuration import load_configuration
from iot.machine.MachineService import MachineService
from iot.mqtt.MqttClient import MqttClient

DB_JSON_FILE = 'data/db.json'


class Main:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def run(self):
        self.logger.debug("Starting")
        config = load_configuration()
        self.logger.debug("Configuration loaded")
        storage = Storage(DB_JSON_FILE, config.name)
        self.logger.debug("Storage loaded")
        machine_service = MachineService(storage, config)
        self.logger.debug("Services loaded")
        client = MqttClient(machine_service, config.mqtt, config.sources, config.destinations)
        self.logger.debug("Mqtt client loaded")

        try:
            client.start()
            self.logger.info("Started.")
            while True:
                sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down.")
        finally:
            storage.shutdown()
            client.stop()


if __name__ == '__main__':
    logging.basicConfig(filename='data/default.log', encoding='utf-8',
                        level=logging.DEBUG if sys.flags.debug else logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    Main().run()
