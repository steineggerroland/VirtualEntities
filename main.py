import paho.mqtt.client as mqtt

from machine.IotMachine import IotMachine
from machine.Dryer import from_dict as d_from_dict
from machine.WashingMachine import from_dict as wm_from_dict
from core.configuration import load_configuration
from core.storage import init as db_init, shutdown as db_shutdown, load_thing, update_thing, append_power_consumption

thing: None | IotMachine


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(config.sources.consumption_topic)


def on_message(client, userdata, msg):
    global thing
    if msg.topic == config.sources.consumption_topic:
        new_power_consumption = float(msg.payload)
        thing.update_power_consumption(new_power_consumption)
        update_thing(thing)
        append_power_consumption(new_power_consumption, thing)


if __name__ == '__main__':
    config = load_configuration()
    db_init(config.name)
    db_entry = load_thing(config.name)
    if config.type == 'washing_machine':
        thing = wm_from_dict(db_entry)
    elif config.type == 'dryer':
        thing = d_from_dict(db_entry)

    client = mqtt.Client(client_id=config.mqtt.client_id)
    if config.mqtt.has_credentials:
        client.username_pw_set(config.mqtt.username, config.mqtt.password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(config.mqtt.url, config.mqtt.port)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        db_shutdown()
        client.disconnect()
