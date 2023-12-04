import datetime

from tinydb import TinyDB, Query

from machine.IotMachine import IotMachine

db: None | TinyDB


def init(thing_name):
    global db
    db = TinyDB('db.json')
    Thing = Query()
    if not db.search(Thing.type == 'thing' and Thing.name == thing_name):
        db.insert({'type': 'thing', 'name': thing_name})


def shutdown():
    global db
    db.close()


def load_thing(thing_name):
    global db
    Thing = Query()
    return db.search(Thing.type == 'thing' and Thing.name == thing_name)[0]


def update_thing(thing: IotMachine):
    global db
    Thing = Query()
    db.update(thing.to_dict(), Thing.type == 'thing' and Thing.name == thing.name)


def append_power_consumption(watt, thing):
    global db
    thing_measurements_table = db.table(f"{thing.name}.measurements")
    thing_measurements_table.insert(
        {"watt": watt, "created_at": datetime.datetime.now().isoformat()})
