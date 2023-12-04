import datetime

from tinydb import TinyDB, Query

from iot.machine.IotMachine import IotMachine


class Storage:
    def __init__(self, db_name: str, thing_name: str):
        self.db = TinyDB(db_name)
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

    def append_power_consumption(self, watt: float, thing: IotMachine):
        thing_measurements_table = self.db.table(f"{thing.name}.measurements")
        thing_measurements_table.insert(
            {"watt": watt, "created_at": datetime.datetime.now().isoformat()})
