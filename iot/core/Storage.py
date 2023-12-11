import datetime

from tinydb import TinyDB, Query

from iot.machine.IotMachine import IotMachine


class Storage:
    def __init__(self, db_name: str, thing_names: [str]):
        self.db = TinyDB(db_name)
        for thing_name in thing_names:
            Thing = Query()
            if not self.db.search(Thing.type == 'thing' and Thing.name == thing_name):
                self.db.insert({'type': 'thing', 'name': thing_name})

    def shutdown(self):
        self.db.close()

    def load_thing(self, thing_name: str):
        Thing = Query()
        return self.db.search(Thing.type == 'thing' and Thing.name == thing_name)[0]

    def update_thing(self, thing: IotMachine):
        Thing = Query()
        self.db.update(thing.to_dict(), Thing.type == 'thing' and Thing.name == thing.name)

    def append_power_consumption(self, watt: float, thing_name):
        thing_measurements_table = self.db.table(f"{thing_name}.measurements")
        thing_measurements_table.insert(
            {"watt": watt, "created_at": datetime.datetime.now().isoformat()})

    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name):
        thing_measurements_table = self.db.table(f"{thing_name}.measurements")
        time_boundary = datetime.datetime.now() - datetime.timedelta(seconds=seconds)
        PowerConsumption = Query()
        return thing_measurements_table.search(
            PowerConsumption.created_at.test(lambda dt: datetime.datetime.fromisoformat(dt) > time_boundary))
