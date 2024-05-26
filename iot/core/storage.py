import json
import time
from pathlib import Path
from threading import Thread
from typing import List

from iot.infrastructure.exceptions import InvalidThingType
from iot.infrastructure.machine.dishwasher import from_dict as dw_from_dict
from iot.infrastructure.machine.dryer import from_dict as d_from_dict
from iot.infrastructure.machine.machine_that_can_be_loaded import MachineThatCanBeLoaded
from iot.infrastructure.machine.washing_machine import from_dict as wm_from_dict
from iot.infrastructure.room import from_dict as r_from_dict, Room
from iot.infrastructure.thing import Thing


class Storage:
    def __init__(self, db_path: Path, thing_names: [str]):
        self.db_name = db_path
        self.things = {}
        db_file = None
        try:
            db_file = open(db_path)
            things_in_db = json.loads(db_file.read())
            for thing_name in thing_names:
                self.things[thing_name] = things_in_db[thing_name] \
                    if thing_name in things_in_db \
                    else {'type': 'thing', 'name': thing_name}
        except FileNotFoundError:
            for thing_name in thing_names:
                self.things[thing_name] = {'type': 'thing', 'name': thing_name}
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

    def load_iot_machine(self, thing_name: str) -> MachineThatCanBeLoaded:
        db_entry = self.things[thing_name]
        if db_entry.type == 'washing_machine':
            return wm_from_dict(db_entry)
        elif db_entry.type == 'dryer':
            return d_from_dict(db_entry)
        elif db_entry.type == 'dishwasher':
            return dw_from_dict(db_entry)
        else:
            raise InvalidThingType(db_entry.type)

    def load_room(self, name: str) -> Room:
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
        iot_machines = list(
            map(lambda r: wm_from_dict(r), filter(lambda e: e["type"] == 'washing_machine', self.things.values())))
        iot_machines.extend(map(lambda r: d_from_dict(r), filter(lambda e: e["type"] == 'dryer', self.things.values())))
        iot_machines.extend(
            map(lambda r: dw_from_dict(r), filter(lambda e: e["type"] == 'dishwasher', self.things.values())))
        return iot_machines

    def load_all_rooms(self) -> List[Room]:
        return list(map(lambda r: r_from_dict(r), filter(lambda e: e["type"] == 'room', self.things.values())))
