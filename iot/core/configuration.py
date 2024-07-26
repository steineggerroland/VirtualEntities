from typing import List, Optional


class IncompleteConfiguration(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class TimeSeriesConfig:
    def __init__(self, url: str, port: Optional[int], username: str, password: str, bucket_name: str):
        self.url = url
        self.port = 8086 if port is None else int(port)
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


class RunCompleteWhen:
    def __init__(self, below_threshold_for_seconds: int = None, watt_threshold: int = None):
        self.below_threshold_for_seconds = below_threshold_for_seconds if below_threshold_for_seconds is not None else 180
        self.watt_threshold = watt_threshold if watt_threshold is not None else 10


class VirtualEntityConfig:
    def __init__(self, name: None | str = None, entity_type: None | str = None,
                 temperature_thresholds: None | ThresholdsConfig = None,
                 humidity_thresholds: None | ThresholdsConfig = None,
                 sources: None | Sources = None,
                 destinations: None | Destinations = None, run_complete_when=RunCompleteWhen(),
                 power_consumption_indicates_loading=None, is_loadable=None):
        self.name = name
        self.type = entity_type
        self.temperature_thresholds = temperature_thresholds
        self.humidity_thresholds = humidity_thresholds
        self.sources = sources
        self.destinations = destinations
        self.run_complete_when = run_complete_when
        self.power_consumption_indicates_loading = power_consumption_indicates_loading if power_consumption_indicates_loading is not None else False
        self.is_loadable = is_loadable

    def __str__(self):
        return f"{self.name} ({self.type}, {self.sources}, {self.destinations})"


class Configuration:
    def __init__(self, mqtt: MqttConfiguration, entities: [VirtualEntityConfig], time_series: TimeSeriesConfig | None,
                 calendars_config: CalendarsConfig, flaskr: dict):
        self.mqtt = mqtt
        self.entities = entities
        self.time_series = time_series
        self.calendars_config = calendars_config
        self.flaskr = flaskr

    def __str__(self):
        return f"{self.mqtt}, {self.entities}, {self.time_series}, {self.calendars_config}"
