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
    return MqttConfiguration(mqtt_dict['url'], mqtt_dict[
        'clientId'] if 'clientId' in mqtt_dict else f"client-{conf_dict['name']}",
                             mqtt_dict['port'] if 'port' in mqtt_dict else None,
                             credentials=_read_mqtt_credentials(mqtt_dict))


def _read_mqtt_credentials(mqtt_dict):
    if 'username' in mqtt_dict and 'password' in mqtt_dict:
        return {'username': mqtt_dict['username'], 'password': mqtt_dict['password']}
    return None


def _read_destination_configuration(conf_dict):
    if 'destinations' not in conf_dict or 'scheduled_updates' not in conf_dict['destinations']:
        return Destinations(list())
    planned_notifications = list()
    for entry in conf_dict['destinations']['scheduled_updates']:
        _verify_keys(entry, ['topic', 'cron'], 'destinations.scheduled_updates[]')
        planned_notifications.append(PlannedNotification(entry['topic'], entry['cron']))
    return Destinations(planned_notifications)


def _read_configuration(conf_dict):
    _verify_keys(conf_dict, ['name', 'type', 'sources'])
    return Configuration(conf_dict['name'], conf_dict['type'], _read_mqtt_configuration(conf_dict),
                         _read_sources_configuration(conf_dict),
                         _read_destination_configuration(conf_dict))


def _read_sources_configuration(conf_dict):
    _verify_keys(conf_dict['sources'], ['consumption'], 'sources')
    _verify_keys(conf_dict['sources']['consumption'], ['topic'], 'sources.consumption')
    consumption_topic = conf_dict['sources']['consumption']['topic']
    loading_topic = None
    if 'loading' in conf_dict['sources']:
        _verify_keys(conf_dict['sources']['loading'], ['topic'], 'sources.loading')
        loading_topic = conf_dict['sources']['loading']['topic']
    unloading_topic = None
    if 'unloading' in conf_dict['sources']:
        _verify_keys(conf_dict['sources']['unloading'], ['topic'], 'sources.unloading')
        unloading_topic = conf_dict['sources']['unloading']['topic']

    return Sources(consumption_topic, loading_topic, unloading_topic)


def _verify_keys(yaml_dict, keys, prefix=None):
    for key in keys:
        if key not in yaml_dict:
            raise IncompleteConfiguration(f"Config is missing key '{prefix + '.' if prefix else ''}{key}'")


class IncompleteConfiguration(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Configuration:
    def __init__(self, name, type, mqtt, sources, destinations):
        self.name = name
        self.type = type
        self.mqtt = mqtt
        self.sources = sources
        self.destinations = destinations

    def __str__(self):
        return f"{self.name} ({self.type}), {self.mqtt}"


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


class Sources:
    def __init__(self, consumption_topic, loading_topic=None, unloading_topic=None):
        self.consumption_topic = consumption_topic
        self.loading_topic = loading_topic
        self.unloading_topic = unloading_topic


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
