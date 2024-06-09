import json
import logging
import time
from pathlib import Path
from threading import Thread
from typing import List

from iot.infrastructure.exceptions import InvalidThingType
from iot.infrastructure.machine.machine_builder import MachineBuilder
from iot.infrastructure.machine.machine_that_can_be_loaded import MachineThatCanBeLoaded
from iot.infrastructure.room import from_dict as r_from_dict, Room
from iot.infrastructure.thing import Thing


class Storage:
    def __init__(self, db_path: Path, thing_names: [str]):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.db_name = db_path
        self.things = {}
        db_file = None
        try:
            db_file = open(db_path)
            things_in_db = json.loads(db_file.read())
            for thing_name in thing_names:
                if thing_name in things_in_db:
                    self.things[thing_name] = things_in_db[thing_name]
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
            json.dump(self.things, db_file)

    def load_iot_machine(self, thing_name: str) -> MachineThatCanBeLoaded | None:
        if thing_name not in self.things:
            return None
        try:
            return MachineBuilder.from_dict(self.things[thing_name])
        except InvalidThingType:
            return None

    def load_room(self, name: str) -> Room | None:
        if name not in self.things:
            return None

        db_entry = self.things[name]
        return r_from_dict(db_entry)

    def update(self, thing: Thing) -> bool:
        is_update = thing.name in self.things.keys()
        self.things[thing.name] = thing.to_dict()
        return is_update

    def remove(self, name: str) -> bool:
        if name in self.things.keys():
            del self.things[name]
            return True
        return False

    def load_all_iot_machines(self) -> List[MachineThatCanBeLoaded]:
        return list(map(MachineBuilder.from_dict,
                        filter(lambda t: MachineBuilder.can_build(t['type']), self.things.values())))

    def load_all_rooms(self) -> List[Room]:
        return list(map(lambda r: r_from_dict(r), filter(lambda e: e['type'] == 'room', self.things.values())))

    def rename(self, old_name: str, new_name: str):
        if new_name != old_name:
            self.things[new_name] = self.things[old_name]
            del self.things[old_name]
