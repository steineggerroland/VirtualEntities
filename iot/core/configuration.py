from typing import List, Any, Optional

import yaml
import yamlenv
from python_event_bus import EventBus

from iot.core.configuration_to_yaml_dumper import ConfigDumpers


class IncompleteConfiguration(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class TimeSeriesConfig:
    def __init__(self, url: str, port: Optional[int], username: str, password: str, bucket_name: str):
        self.url = url
        self.port = port if port is None else int(port)
        self.username = username
        self.password = password
        self.bucket_name = bucket_name


class MqttConfiguration:
    def __init__(self, url: str, client_id: str, port: int = 1883, credentials: dict | None = None):
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


class Measure:
    def __init__(self, source_type: str, path: None | str = None):
        self.type = source_type
        self.path = path


class Source:
    pass


class MqttMeasureSource(Source):
    def __init__(self, mqtt_topic: str, measures: list[Measure]):
        self.mqtt_topic = mqtt_topic
        self.measures = measures

    def __eq__(self, other):
        if not isinstance(other, MqttMeasureSource) or self.mqtt_topic != other.mqtt_topic:
            return False
        for measure in self.measures:
            if not any(vars(measure) == vars(other_measure) for other_measure in other.measures):
                return False
        return True


class UrlConf(Source):

    def __init__(self, application: str, name: str, url: str, username: str = None, password: str = None,
                 update_cron: str = None):
        self.application = application
        self.name = name
        self.url = url
        self.username = username
        self.password = password
        self.update_cron = update_cron if update_cron is not None else "0 */15 * * * *"  # update hourly by default

    def __eq__(self, other):
        if not isinstance(other, UrlConf):
            return False
        return self.application == other.application and self.name == other.name and self.url == other.url and \
            self.username == other.username and self.password == other.username

    def has_credentials(self):
        return self.username is not None


class ReferencedUrlConf(UrlConf):
    def __init__(self, conf: UrlConf):
        super().__init__(conf.application, conf.name, conf.url, conf.username, conf.password, conf.update_cron)


class CaldavConfig(UrlConf):
    def __init__(self, url_conf: UrlConf, color_hex: str = None):
        super().__init__("calendar", url_conf.name, url_conf.url, url_conf.username, url_conf.password,
                         url_conf.update_cron)
        self.color_hex = color_hex.lower() if color_hex is not None else "ffffff"


class ReferencedCaldavConfig(CaldavConfig):
    def __init__(self, caldav_conf: CaldavConfig):
        super().__init__(caldav_conf, caldav_conf.color_hex)


class CategoryConfig:
    def __init__(self, name: str, color_hex: str):
        self.name = name
        self.color_hex = color_hex.lower()


class CalendarsConfig:
    def __init__(self, categories: list[CategoryConfig], calendars: list[CaldavConfig]):
        self.categories = categories
        self.calendars = calendars


class Sources:
    def __init__(self, sources: List[Source]):
        self.list = sources


class PlannedNotification:
    def __init__(self, mqtt_topic: str, cron_expression: str, subject: str | None = None):
        self.mqtt_topic = mqtt_topic
        self.cron_expression = cron_expression
        self.subject = subject

    def __eq__(self, other):
        if not isinstance(other, PlannedNotification):
            return False
        return (self.mqtt_topic == other.mqtt_topic and self.cron_expression == other.cron_expression
                and self.subject == other.subject)


class Destinations:
    def __init__(self, planned_notifications: List[PlannedNotification]):
        self.planned_notifications = planned_notifications


class RangeConfig:
    def __init__(self, lower: float, upper: float):
        self.lower = lower
        self.upper = upper


class ThresholdsConfig:
    def __init__(self, optimal: RangeConfig, critical_lower: float, critical_upper: float):
        self.optimal = optimal
        self.critical_lower = critical_lower
        self.critical_upper = critical_upper


class IotThingConfig:
    def __init__(self, name: None | str = None, thing_type: None | str = None,
                 temperature_thresholds: None | ThresholdsConfig = None,
                 humidity_thresholds: None | ThresholdsConfig = None,
                 sources: None | Sources = None,
                 destinations: None | Destinations = None):
        self.name = name
        self.type = thing_type
        self.temperature_thresholds = temperature_thresholds
        self.humidity_thresholds = humidity_thresholds
        self.sources = sources
        self.destinations = destinations

    def __str__(self):
        return f"{self.name} ({self.type}, {self.sources}, {self.destinations})"


class Configuration:
    def __init__(self, mqtt: MqttConfiguration, things: [IotThingConfig], time_series: TimeSeriesConfig | None,
                 calendars_config: CalendarsConfig, flaskr: dict):
        self.mqtt = mqtt
        self.things = things
        self.time_series = time_series
        self.calendars_config = calendars_config
        self.flaskr = flaskr

    def __str__(self):
        return f"{self.mqtt}, {self.things}, {self.time_series}, {self.calendars_config}"


def _read_mqtt_configuration(conf_dict) -> MqttConfiguration:
    mqtt_dict = conf_dict['mqtt']
    _verify_keys(mqtt_dict, ['url'], 'mqtt')
    return MqttConfiguration(mqtt_dict['url'],
                             mqtt_dict['client_id'] if 'client_id' in mqtt_dict else f"iot-things-client",
                             mqtt_dict['port'] if 'port' in mqtt_dict else None,
                             credentials=_read_mqtt_credentials(mqtt_dict))


def _read_mqtt_credentials(mqtt_dict) -> dict | None:
    if 'username' in mqtt_dict and 'password' in mqtt_dict:
        return {'username': mqtt_dict['username'], 'password': mqtt_dict['password']}
    return None


def _read_destination_configuration(thing_dict) -> Destinations:
    if 'destinations' not in thing_dict or 'planned_notifications' not in thing_dict['destinations']:
        return Destinations([])
    planned_notifications = []
    for entry in thing_dict['destinations']['planned_notifications']:
        _verify_keys(entry, ['mqtt_topic', 'cron_expression'],
                     'things[%s].destinations.planned_notification[]' % thing_dict['name'])
        planned_notifications.append(
            PlannedNotification(entry['mqtt_topic'], entry['cron_expression'],
                                entry['subject'] if 'subject' in entry else None))
    return Destinations(planned_notifications)


def _read_sources_configuration(thing_dict, calendars: List[CaldavConfig]) -> Sources:
    if 'sources' not in thing_dict:
        return Sources([])

    if not thing_dict['sources']:
        raise IncompleteConfiguration("Sources configuration is not a list")

    sources = []
    for source in thing_dict['sources']:
        if "mqtt_topic" in source:
            sources.append(_read_mqtt_source(source))
        elif "application" in source and source["application"] == "calendar":
            _verify_keys_set(source, [['reference_name'], ['url', 'name']],
                             "things[%s].sources[%s]" % (thing_dict['name'], source["application"]))

            if 'reference_name' in source:
                conf = _get_referenced_calendar_conf(source["reference_name"], calendars, "things[%s].sources[%s]" % (
                    thing_dict['name'], source["application"]))
            else:
                conf = CaldavConfig(_read_new_url_conf(source, "calendar"),
                                    source["color_hex"] if "color_hex" in source else None)
            sources.append(conf)
        else:
            raise IncompleteConfiguration("Unknown source '%s' of thing '%s'" % (source, thing_dict['name']))

    return Sources(sources)


def _get_referenced_calendar_conf(reference_name: str, calendars: list[CaldavConfig], path) -> ReferencedCaldavConfig:
    referenced_configs: list[CaldavConfig] = list(filter(lambda c: c.name == reference_name, calendars))
    if len(referenced_configs) < 1:
        raise IncompleteConfiguration(f"No general calendar configuration '{reference_name}' referenced in '{path}'")
    else:
        return ReferencedCaldavConfig(referenced_configs[0])


def _read_new_url_conf(url_conf, application):
    update_cron = url_conf["update_cron"] if "update_cron" in url_conf else None
    return UrlConf(application, url_conf["name"], url_conf["url"],
                   update_cron=update_cron) if "username" not in url_conf \
        else UrlConf(application, url_conf["name"], url_conf["url"], url_conf["username"], url_conf["password"],
                     update_cron)


def _read_mqtt_source(source):
    measures = []
    if 'measures' in source:
        for measure in source['measures']:
            _verify_keys(measure, ['type'], "things[].sources[].measures[]")
            measures.append(Measure(source_type=measure['type'],
                                    path=measure['path'] if 'path' in measure else None))
    else:
        _verify_keys(source, ['type'], "things[].sources[]")
        measures.append(
            Measure(source_type=source['type'], path=source['path'] if 'path' in source else None))
    return MqttMeasureSource(mqtt_topic=source['mqtt_topic'], measures=measures)


def _read_thresholds_config(thresholds_config: dict, prefix) -> ThresholdsConfig:
    _verify_keys(["optimal", "critical_lower", "critical_upper"], thresholds_config, prefix)
    _verify_keys(["lower", "upper"], thresholds_config['optimal'], f"{prefix}.optimal")
    return ThresholdsConfig(RangeConfig(thresholds_config['optimal']['lower'], thresholds_config['optimal']['upper']),
                            thresholds_config['critical_lower'], thresholds_config['critical_upper'])


def _read_temperature_thresholds_configuration(thing_config: dict) -> None | ThresholdsConfig:
    if "temperature_thresholds" in thing_config:
        return _read_thresholds_config(thing_config['temperature_thresholds'], "things[].temperature_thresholds")
    else:
        return None


def _read_humidity_thresholds_configuration(thing_config: dict) -> None | ThresholdsConfig:
    if "humidity_thresholds" in thing_config:
        return _read_thresholds_config(thing_config['humidity_thresholds'], "things[].humidity_thresholds")
    else:
        return None


def _read_caldav_configuration(caldav_config: dict) -> List[CaldavConfig]:
    if type(caldav_config) is not list:
        raise IncompleteConfiguration("'calendars.dav' must be a list")
    return list(
        map(lambda calendar_config: CaldavConfig(_read_new_url_conf(calendar_config, "calendar"),
                                                 calendar_config[
                                                     "color_hex"] if "color_hex" in calendar_config else None),
            caldav_config))


def _read_category_config(category_config: dict) -> CategoryConfig:
    _verify_keys(category_config, ["name", "color_hex"], 'calendars.categories')
    return CategoryConfig(category_config["name"], category_config["color_hex"])


def _read_calendar_categories_configuration(categories_config):
    if type(categories_config) is not list:
        raise IncompleteConfiguration("'calendars.categories' must be a list")
    return list(map(_read_category_config, categories_config))


def _read_calendars_configuration(thing_config: dict) -> CalendarsConfig:
    if "calendars" not in thing_config:
        return CalendarsConfig([], [])
    calendars_config = thing_config["calendars"]
    calendars = _read_caldav_configuration(calendars_config["caldav"]) if "caldav" in calendars_config else []
    categories = _read_calendar_categories_configuration(
        calendars_config["categories"]) if "categories" in calendars_config else []
    return CalendarsConfig(categories, calendars)


def _read_thing(thing_config, calendars) -> IotThingConfig:
    _verify_keys(thing_config, ["name", "type"], "things[]")
    return IotThingConfig(thing_config['name'], thing_config['type'],
                          _read_temperature_thresholds_configuration(thing_config),
                          _read_humidity_thresholds_configuration(thing_config),
                          _read_sources_configuration(thing_config, calendars),
                          _read_destination_configuration(thing_config))


def _read_things(conf_dict, calendars) -> List[IotThingConfig]:
    _verify_keys(conf_dict, ["things"])
    return [_read_thing(thing_config, calendars) for thing_config in conf_dict['things']]


def _read_time_series_config(time_series_config) -> TimeSeriesConfig:
    _verify_keys(time_series_config, ['url', 'username', 'password', 'bucket_name'], 'time_series')
    return TimeSeriesConfig(time_series_config['url'],
                            time_series_config['port'] if 'port' in time_series_config else None,
                            time_series_config['username'],
                            time_series_config['password'], time_series_config['bucket_name'])


def _read_configuration(conf_dict) -> Configuration:
    calendars_config = _read_calendars_configuration(conf_dict)
    return Configuration(_read_mqtt_configuration(conf_dict),
                         _read_things(conf_dict, calendars_config.calendars),
                         _read_time_series_config(conf_dict['time_series']) if 'time_series' in conf_dict else None,
                         calendars_config,
                         conf_dict['flaskr'] if 'flaskr' in conf_dict else {})


def _verify_keys_set(yaml_dict, key_sets, prefix=None):
    if not any(all(key in yaml_dict for key in keys) for keys in key_sets):
        raise IncompleteConfiguration(
            f"Config is missing key(s) in '{prefix + '.' if prefix else ''}'. There must any set of keys: {key_sets}")


def _verify_keys(yaml_dict, keys, prefix=None):
    if any(key not in yaml_dict for key in keys):
        raise IncompleteConfiguration(
            f"Config is missing key(s) in '{prefix + '.' if prefix else ''}'. Mandatory are {keys}")


sd = safe_dumper = yaml.SafeDumper
for item in [(Configuration, ConfigDumpers.configuration_dumper), (TimeSeriesConfig, ConfigDumpers.time_series_dumper),
             (MqttConfiguration, ConfigDumpers.mqtt_dumper), (Measure, ConfigDumpers.measure_dumper),
             (MqttMeasureSource, ConfigDumpers.mqtt_measure_source_dumper), (UrlConf, ConfigDumpers.url_conf_dumper),
             (ReferencedUrlConf, ConfigDumpers.referenced_url_dumper), (CaldavConfig, ConfigDumpers.caldav_dumper),
             (ReferencedCaldavConfig, ConfigDumpers.referenced_caldav_dumper),
             (CategoryConfig, ConfigDumpers.category_dumper), (CalendarsConfig, ConfigDumpers.calendars_dumper),
             (Sources, ConfigDumpers.sources_dumper), (PlannedNotification, ConfigDumpers.planned_notification_dumper),
             (Destinations, ConfigDumpers.destinations_dumper), (RangeConfig, ConfigDumpers.range_dumper),
             (ThresholdsConfig, ConfigDumpers.thresholds_dumper), (IotThingConfig, ConfigDumpers.iot_thing_dumper)]:
    sd.add_representer(item[0], item[1])


def _save_configuration(conf: Configuration, config_path):
    with open(config_path, 'w') as new_conf:
        new_conf.write(yaml.dump(conf, Dumper=sd))


class ConfigurationManager:
    def __init__(self):
        self.configuration: Configuration | None = None
        self.config_path: Any | None = None

    def load(self, config_path) -> Configuration:
        self.config_path = config_path
        conf_file = None
        try:
            conf_file = open(config_path)
            conf_dict = yamlenv.load(conf_file)
            self.configuration = _read_configuration(conf_dict)
        except FileNotFoundError as e:
            raise Exception(f'Configuration file is missing. File "{config_path}" is needed.') from e
        finally:
            if conf_file:
                conf_file.close()
        return self.configuration

    def rename_appliance(self, old_name: str, new_name: str):
        if new_name != old_name:
            thing = list(filter(lambda t: t.name == old_name, self.configuration.things)).pop()
            thing.name = new_name
            self.save()
            EventBus.call("appliance/changed_config_name", name=new_name, old_name=old_name)

    def rename_room(self, old_name, new_name):
        if new_name != old_name:
            thing = list(filter(lambda t: t.name == old_name, self.configuration.things)).pop()
            thing.name = new_name
            self.save()
            EventBus.call("room/changed_config_name", name=new_name, old_name=old_name)

    def save(self):
        _save_configuration(self.configuration, self.config_path)
