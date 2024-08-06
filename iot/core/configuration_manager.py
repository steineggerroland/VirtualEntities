from typing import Any

import yaml
import yamlenv
from python_event_bus import EventBus

from iot.core.configuration import *
from iot.core.configuration_to_yaml_dumper import ConfigDumpers
from iot.infrastructure.appliance.appliance_events import ApplianceEvents
from iot.infrastructure.room_events import RoomEvents


def _read_mqtt_configuration(conf_dict) -> MqttConfiguration:
    mqtt_dict = conf_dict['mqtt']
    _verify_keys(mqtt_dict, ['url'], 'mqtt')
    return MqttConfiguration(mqtt_dict['url'],
                             mqtt_dict['client_id'] if 'client_id' in mqtt_dict else f"entities-client",
                             mqtt_dict['port'] if 'port' in mqtt_dict else None,
                             credentials=_read_mqtt_credentials(mqtt_dict))


def _read_mqtt_credentials(mqtt_dict) -> dict | None:
    if 'username' in mqtt_dict and 'password' in mqtt_dict:
        return {'username': mqtt_dict['username'], 'password': mqtt_dict['password']}
    return None


def _read_run_complete_threshold(entity_dict) -> RunCompleteWhen:
    if 'run_complete_when' in entity_dict:
        return RunCompleteWhen(
            entity_dict['run_complete_when']['below_threshold_for'] if 'below_threshold_for' in entity_dict[
                'run_complete_when'] else None,
            entity_dict['run_complete_when']['threshold'] if 'threshold' in entity_dict['run_complete_when'] else None)
    else:
        return RunCompleteWhen()


def _read_destination_configuration(entity_dict) -> Destinations:
    if 'destinations' not in entity_dict or 'planned_notifications' not in entity_dict['destinations']:
        return Destinations([])
    planned_notifications = []
    for entry in entity_dict['destinations']['planned_notifications']:
        _verify_keys(entry, ['mqtt_topic', 'cron_expression'],
                     'entities[%s].destinations.planned_notification[]' % entity_dict['name'])
        planned_notifications.append(
            PlannedNotification(entry['mqtt_topic'], entry['cron_expression'],
                                entry['subject'] if 'subject' in entry else None))
    return Destinations(planned_notifications)


def _read_sources_configuration(entity_dict, calendars: List[CaldavConfig]) -> Sources:
    if 'sources' not in entity_dict:
        return Sources([])

    if not entity_dict['sources']:
        raise IncompleteConfiguration("Sources configuration is not a list")

    sources = []
    for source in entity_dict['sources']:
        if "mqtt_topic" in source:
            sources.append(_read_mqtt_source(source))
        elif "application" in source and source["application"] == "calendar":
            _verify_keys_set(source, [['reference_name'], ['url', 'name']],
                             "entities[%s].sources[%s]" % (entity_dict['name'], source["application"]))

            if 'reference_name' in source:
                conf = _get_referenced_calendar_conf(source["reference_name"], calendars, "entities[%s].sources[%s]" % (
                    entity_dict['name'], source["application"]))
            else:
                conf = CaldavConfig(_read_new_url_conf(source, "calendar"),
                                    source["color_hex"] if "color_hex" in source else None)
            sources.append(conf)
        else:
            raise IncompleteConfiguration("Unknown source '%s' of entity '%s'" % (source, entity_dict['name']))

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
            _verify_keys(measure, ['type'], "entities[].sources[].measures[]")
            measures.append(Measure(source_type=measure['type'],
                                    path=measure['path'] if 'path' in measure else None))
    else:
        _verify_keys(source, ['type'], "entities[].sources[]")
        measures.append(
            Measure(source_type=source['type'], path=source['path'] if 'path' in source else None))
    return MqttMeasureSource(mqtt_topic=source['mqtt_topic'], measures=measures)


def _read_thresholds_config(thresholds_config: dict, prefix) -> ThresholdsConfig:
    _verify_keys(["optimal", "critical_lower", "critical_upper"], thresholds_config, prefix)
    _verify_keys(["lower", "upper"], thresholds_config['optimal'], f"{prefix}.optimal")
    return ThresholdsConfig(RangeConfig(thresholds_config['optimal']['lower'], thresholds_config['optimal']['upper']),
                            thresholds_config['critical_lower'], thresholds_config['critical_upper'])


def _read_temperature_thresholds_configuration(entity_config: dict) -> None | ThresholdsConfig:
    if "temperature_thresholds" in entity_config:
        return _read_thresholds_config(entity_config['temperature_thresholds'], "entities[].temperature_thresholds")
    else:
        return None


def _read_humidity_thresholds_configuration(entity_config: dict) -> None | ThresholdsConfig:
    if "humidity_thresholds" in entity_config:
        return _read_thresholds_config(entity_config['humidity_thresholds'], "entities[].humidity_thresholds")
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


def _read_calendars_configuration(entity_config: dict) -> CalendarsConfig:
    if "calendars" not in entity_config:
        return CalendarsConfig([], [])
    calendars_config = entity_config["calendars"]
    calendars = _read_caldav_configuration(calendars_config["caldav"]) if "caldav" in calendars_config else []
    categories = _read_calendar_categories_configuration(
        calendars_config["categories"]) if "categories" in calendars_config else []
    return CalendarsConfig(categories, calendars)


def _read_entity(entity_config: dict, calendars) -> VirtualEntityConfig:
    _verify_keys(entity_config, ["name", "type"], "entities[]")
    return VirtualEntityConfig(entity_config['name'], entity_config['type'],
                               _read_temperature_thresholds_configuration(entity_config),
                               _read_humidity_thresholds_configuration(entity_config),
                               _read_sources_configuration(entity_config, calendars),
                               _read_destination_configuration(entity_config),
                               _read_run_complete_threshold(entity_config),
                               entity_config.get('power_consumption_indicates_charging', None),
                               entity_config.get('is_loadable', None),
                               entity_config.get('is_cleanable', None))


def _read_entities(conf_dict: dict, calendars) -> List[VirtualEntityConfig]:
    _verify_keys(conf_dict, ["entities"])
    return [_read_entity(entity_config, calendars) for entity_config in conf_dict['entities']]


def _read_time_series_config(time_series_config) -> TimeSeriesConfig:
    _verify_keys(time_series_config, ['url', 'username', 'password', 'bucket_name'], 'time_series')
    return TimeSeriesConfig(time_series_config['url'],
                            time_series_config['port'] if 'port' in time_series_config else None,
                            time_series_config['username'],
                            time_series_config['password'], time_series_config['bucket_name'])


def _read_configuration(conf_dict: dict) -> Configuration:
    calendars_config = _read_calendars_configuration(conf_dict)
    return Configuration(_read_mqtt_configuration(conf_dict),
                         _read_entities(conf_dict, calendars_config.calendars),
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
             (ThresholdsConfig, ConfigDumpers.thresholds_dumper), (VirtualEntityConfig, ConfigDumpers.entity_dumper),
             (RunCompleteWhen, ConfigDumpers.run_complete_when_dumper)]:
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
            conf_dict: dict = yamlenv.load(conf_file)
            self.configuration = _read_configuration(conf_dict)
        except FileNotFoundError as e:
            raise Exception(f'Configuration file is missing. File "{config_path}" is needed.') from e
        finally:
            if conf_file:
                conf_file.close()
        return self.configuration

    def rename_appliance(self, old_name: str, new_name: str):
        if new_name != old_name:
            entity = list(filter(lambda t: t.name == old_name, self.configuration.entities)).pop()
            entity.name = new_name
            self.save()
            EventBus.call(ApplianceEvents.CHANGED_CONFIG_NAME, name=new_name, old_name=old_name)

    def rename_room(self, old_name, new_name):
        if new_name != old_name:
            entity = list(filter(lambda t: t.name == old_name, self.configuration.entities)).pop()
            entity.name = new_name
            self.save()
            EventBus.call(RoomEvents.CHANGED_CONFIG_NAME, name=new_name, old_name=old_name)

    def rename_person(self, old_name, new_name):
        if new_name != old_name:
            entity = list(filter(lambda t: t.name == old_name, self.configuration.entities)).pop()
            entity.name = new_name
            self.save()
            EventBus.call("person/changed_config_name", name=new_name, old_name=old_name)

    def save(self):
        _save_configuration(self.configuration, self.config_path)
