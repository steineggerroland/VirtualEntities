import yamlenv


def load_configuration(config_path):
    conf_file = None
    try:
        conf_file = open(config_path)
        conf_dict = yamlenv.load(conf_file)

        config = _read_configuration(conf_dict)
        return config
    except FileNotFoundError as e:
        raise Exception(f'Configuration file is missing. File "{config_path}" is needed.') from e
    finally:
        if conf_file:
            conf_file.close()


def _read_mqtt_configuration(conf_dict):
    mqtt_dict = conf_dict['mqtt']
    _verify_keys(mqtt_dict, ['url'], 'mqtt')
    return MqttConfiguration(mqtt_dict['url'],
                             mqtt_dict['clientId'] if 'clientId' in mqtt_dict else f"iot-things-client",
                             mqtt_dict['port'] if 'port' in mqtt_dict else None,
                             credentials=_read_mqtt_credentials(mqtt_dict))


def _read_mqtt_credentials(mqtt_dict):
    if 'username' in mqtt_dict and 'password' in mqtt_dict:
        return {'username': mqtt_dict['username'], 'password': mqtt_dict['password']}
    return None


def _read_destination_configuration(thing_dict):
    if 'destinations' not in thing_dict or 'scheduled_updates' not in thing_dict['destinations']:
        return Destinations([])
    planned_notifications = []
    for entry in thing_dict['destinations']['scheduled_updates']:
        _verify_keys(entry, ['topic', 'cron'], 'things[].destinations.scheduled_updates[]')
        planned_notifications.append(PlannedNotification(entry['topic'], entry['cron']))
    return Destinations(planned_notifications)


def _read_sources_configuration(thing_dict):
    if 'sources' not in thing_dict:
        return Sources([])
    sources = []
    if thing_dict['sources']:
        for source in thing_dict['sources']:
            _verify_keys(source, ['topic', 'type'], "things[].sources[]")
            sources.append(Source(topic=source['topic'], source_type=source['type'],
                                  path=source['path'] if 'path' in source else None))

    return Sources(sources)


def _read_thing(thing_config):
    _verify_keys(thing_config, ["name", "type"], "things[]")
    return IotThingConfig(thing_config['name'], thing_config['type'], _read_sources_configuration(thing_config),
                          _read_destination_configuration(thing_config))


def _read_things(conf_dict):
    _verify_keys(conf_dict, ["things"])
    return [_read_thing(thing_config) for thing_config in conf_dict['things']]


def _read_configuration(conf_dict):
    return Configuration(_read_mqtt_configuration(conf_dict),
                         _read_things(conf_dict))


def _verify_keys(yaml_dict, keys, prefix=None):
    for key in keys:
        if key not in yaml_dict:
            raise IncompleteConfiguration(f"Config is missing key '{prefix + '.' if prefix else ''}{key}'")


class IncompleteConfiguration(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Configuration:
    def __init__(self, mqtt, things):
        self.mqtt = mqtt
        self.things = things

    def __str__(self):
        return f"{self.mqtt}, {self.things}"


class MqttConfiguration:
    def __init__(self, url, client_id, port=1883, credentials=None):
        self.url = url
        self.port = port if port is not None else 1883
        if credentials is not None:
            self.username = credentials['username']
            self.password = credentials['password']
            self.has_credentials = True
        else:
            self.has_credentials = False
        self.client_id = client_id

    def __str__(self):
        if self.has_credentials:
            return f"mqtt ({self.url}:{self.port}, {self.username}:<pw len {len(self.password)}>)"
        return f"mqtt ({self.url}:{self.port})"


class Source:
    def __init__(self, topic: str, source_type: str, path: None | str = None):
        self.topic = topic
        self.type = source_type
        self.path = path

    def __eq__(self, other):
        if not isinstance(other, Source):
            return False
        return vars(self) == vars(other)


class Sources:
    def __init__(self, sources: [Source]):
        self.list = sources


class PlannedNotification:
    def __init__(self, mqtt_topic: str, cron_expression: str):
        self.mqtt_topic = mqtt_topic
        self.cron_expression = cron_expression

    def __eq__(self, other):
        if not isinstance(other, PlannedNotification):
            return False
        return self.mqtt_topic == other.mqtt_topic and self.cron_expression == other.cron_expression


class Destinations:
    def __init__(self, planned_notifications: list[PlannedNotification]):
        self.planned_notifications = planned_notifications


class IotThingConfig:
    def __init__(self, name: None | str = None, thing_type: None | str = None, sources: None | Sources = None,
                 destinations: None | Destinations = None):
        self.name = name
        self.type = thing_type
        self.sources = sources
        self.destinations = destinations

    def __str__(self):
        return f"{self.name} ({self.type}, {self.sources}, {self.destinations})"
