import datetime
import json
from pathlib import Path

from iot.infrastructure.thing import Thing


class Storage:
    def __init__(self, db_path: Path, thing_names: [str]):
        self.db_name = db_path
        self.things = {}
        self.power_consumption_values = {}
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

    def shutdown(self):
        with open(self.db_name, 'w') as db_file:
            json.dump(self.things, db_file)

    def load_thing(self, thing_name: str):
        return self.things[thing_name]

    def update_thing(self, thing: Thing):
        self.things[thing.name] = thing.to_dict()

    def append_power_consumption(self, watt: float, thing_name):
        power_consumption_values = self.power_consumption_values[thing_name] \
            if thing_name in self.power_consumption_values else []
        power_consumption_values.append({"watt": watt, "created_at": datetime.datetime.now().isoformat()})
        if len(power_consumption_values) > 10:
            power_consumption_values.pop()
        self.power_consumption_values[thing_name] = power_consumption_values

    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name):
        power_consumption_values = self.power_consumption_values[thing_name] \
            if thing_name in self.power_consumption_values else []
        time_boundary = datetime.datetime.now() - datetime.timedelta(seconds=seconds)
        return [power_consumption for power_consumption in power_consumption_values if
                datetime.datetime.fromisoformat(power_consumption["created_at"]) > time_boundary]
