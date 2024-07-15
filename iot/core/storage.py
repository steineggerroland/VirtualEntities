import json
import logging
import time
from pathlib import Path
from threading import Thread
from typing import List

from python_event_bus import EventBus

from iot.infrastructure.exceptions import InvalidEntityType
from iot.infrastructure.appliance.appliance_builder import ApplianceBuilder
from iot.infrastructure.appliance.appliance_that_can_be_loaded import ApplianceThatCanBeLoaded
from iot.infrastructure.room import from_dict as r_from_dict, Room
from iot.infrastructure.virtual_entity import VirtualEntity


class Storage:
    def __init__(self, db_path: Path, entity_names: [str]):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.db_name = db_path
        self.entities = {}
        db_file = None
        try:
            db_file = open(db_path)
            entities_in_db = json.loads(db_file.read())
            for entity_name in entity_names:
                if entity_name in entities_in_db:
                    self.entities[entity_name] = entities_in_db[entity_name]
        except FileNotFoundError:
            self.logger.debug('Skipping to load files from db: Database file does not exist')
        finally:
            if db_file:
                db_file.close()
        self._scheduled_snapshots_thread: Thread = Thread(target=self._scheduled_snapshots, daemon=True)

    def start(self):
        self._scheduled_snapshots_thread.start()

    def shutdown(self, timeout=5):
        self._scheduled_snapshots_thread.join(timeout)
        self._save_snapshot_to_file()

    def _scheduled_snapshots(self):
        while True:
            time.sleep(60)
            self._save_snapshot_to_file()

    def _save_snapshot_to_file(self):
        with open(self.db_name, 'w') as db_file:
            json.dump(self.entities, db_file)

    def load_appliance(self, entity_name: str) -> ApplianceThatCanBeLoaded | None:
        if entity_name not in self.entities:
            return None
        try:
            return ApplianceBuilder.from_dict(self.entities[entity_name])
        except InvalidEntityType:
            return None

    def load_room(self, name: str) -> Room | None:
        if name not in self.entities:
            return None

        db_entry = self.entities[name]
        return r_from_dict(db_entry)

    def update(self, entity: VirtualEntity) -> bool:
        is_update = entity.name in self.entities.keys()
        self.entities[entity.name] = entity.to_dict()
        return is_update

    def remove(self, name: str) -> bool:
        if name in self.entities.keys():
            del self.entities[name]
            return True
        return False

    def load_all_appliances(self) -> List[ApplianceThatCanBeLoaded]:
        return list(map(ApplianceBuilder.from_dict,
                        filter(lambda t: ApplianceBuilder.can_build(t['type']), self.entities.values())))

    def load_all_rooms(self) -> List[Room]:
        return list(map(lambda r: r_from_dict(r), filter(lambda e: e['type'] == 'room', self.entities.values())))

    def rename(self, name: str, old_name: str):
        self.entities[name] = self.entities[old_name]
        self.entities[name]["name"] = name
        del self.entities[old_name]
