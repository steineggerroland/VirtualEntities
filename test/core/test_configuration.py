import os
import unittest
from pathlib import Path

import yamlenv

from iot.core.configuration import PlannedNotification, IncompleteConfiguration, MqttMeasureSource, Measure
from iot.core.configuration_manager import ConfigurationManager

DIR = Path(__file__).parent


class ConfigurationTest(unittest.TestCase):
    def test_complete_config(self):
        config = ConfigurationManager().load(DIR / "complete_test_config.yaml")
        self.assertEqual("my.appliance.local", config.mqtt.url)
        self.assertEqual(1337, config.mqtt.port)
        self.assertEqual("user", config.mqtt.username)
        self.assertTrue(config.mqtt.has_credentials)
        self.assertEqual("my-secret", config.mqtt.password)
        self.assertEqual("my-client", config.mqtt.client_id)

        self.assertEqual("influxdb.url", config.time_series.url)
        self.assertEqual(8712, config.time_series.port)
        self.assertEqual("influxdb", config.time_series.username)
        self.assertEqual("secret", config.time_series.password)
        self.assertEqual("bucket_to_save_to", config.time_series.bucket_name)

        self.assertEqual("super_entity", config.entities[0].name)
        self.assertEqual("dryer", config.entities[0].type)
        self.assertEqual(5, config.entities[0].run_complete_when.below_threshold_for_seconds)
        self.assertEqual(10, config.entities[0].run_complete_when.watt_threshold)
        self.assertEqual(True, config.entities[0].is_loadable)
        self.assertIn(MqttMeasureSource('consumption/topic', [Measure(source_type='consumption')]),
                      config.entities[0].sources.list)
        self.assertIn(MqttMeasureSource('loading/topic', [Measure(source_type='loading')]),
                      config.entities[0].sources.list)
        self.assertIn(MqttMeasureSource('unloading/topic', [Measure(source_type='unloading')]),
                      config.entities[0].sources.list)

        self.assertIn(PlannedNotification('update/every-second/topic', '*/1 * * * * *'),
                      config.entities[0].destinations.planned_notifications)
        self.assertIn(PlannedNotification('update/every-15-minutes/topic', '* */15 * * * *'),
                      config.entities[0].destinations.planned_notifications)

        self.assertEqual("Coffee machine", config.entities[1].name)
        self.assertEqual("this_is_some_unknown_type", config.entities[1].type)
        self.assertEqual(True, config.entities[1].power_consumption_indicates_charging)
        self.assertEqual(True, config.entities[1].is_cleanable)

        self.assertEqual("Kitchen", config.entities[2].name)
        self.assertEqual("room", config.entities[2].type)
        self.assertEqual("kitchen/sensor/temperature", config.entities[2].sources.list[0].mqtt_topic)
        self.assertEqual("temperature", config.entities[2].sources.list[0].measures[0].type)
        self.assertEqual("$.update.temperature", config.entities[2].sources.list[0].measures[0].path)

        self.assertEqual("Bathroom", config.entities[3].name)
        self.assertEqual("room", config.entities[3].type)
        self.assertEqual(15, config.entities[3].temperature_thresholds.critical_lower)
        self.assertEqual(20, config.entities[3].temperature_thresholds.optimal.lower)
        self.assertEqual(22, config.entities[3].temperature_thresholds.optimal.upper)
        self.assertEqual(30, config.entities[3].temperature_thresholds.critical_upper)
        self.assertEqual(50, config.entities[3].humidity_thresholds.critical_lower)
        self.assertEqual(65, config.entities[3].humidity_thresholds.optimal.lower)
        self.assertEqual(75, config.entities[3].humidity_thresholds.optimal.upper)
        self.assertEqual(90, config.entities[3].humidity_thresholds.critical_upper)
        self.assertEqual("bath/sensor/temperature", config.entities[3].sources.list[0].mqtt_topic)
        self.assertEqual("temperature", config.entities[3].sources.list[0].measures[0].type)
        self.assertEqual("$.temperature", config.entities[3].sources.list[0].measures[0].path)
        self.assertEqual("humidity", config.entities[3].sources.list[0].measures[1].type)
        self.assertEqual("$.humidity", config.entities[3].sources.list[0].measures[1].path)

        self.assertEqual("Jane", config.entities[4].name)
        self.assertEqual("person", config.entities[4].type)
        self.assertEqual("calendar", config.entities[4].sources.list[0].application)
        self.assertEqual("jane private", config.entities[4].sources.list[0].name)
        self.assertEqual("calendar.jane.private", config.entities[4].sources.list[0].url)
        self.assertEqual("calendar-user", config.entities[4].sources.list[0].username)
        self.assertEqual("secret-calendar", config.entities[4].sources.list[0].password)
        self.assertEqual("*/16 * * * *", config.entities[4].sources.list[0].update_cron)
        self.assertEqual("ffffff", config.entities[4].sources.list[0].color_hex)
        # referenced calendar
        self.assertEqual("calendar", config.entities[4].sources.list[1].application)
        self.assertEqual("jane job", config.entities[4].sources.list[1].name)
        self.assertEqual("calendar.job/jane", config.entities[4].sources.list[1].url)
        self.assertEqual("jane", config.entities[4].sources.list[1].username)
        self.assertEqual("secret", config.entities[4].sources.list[1].password)
        self.assertEqual("0 0 * * * *", config.entities[4].sources.list[1].update_cron)
        self.assertEqual("f0f0f0", config.entities[4].sources.list[1].color_hex)
        # notifications
        self.assertEqual("persons/jane/appointments",
                         config.entities[4].destinations.planned_notifications[0].mqtt_topic)
        self.assertEqual("*/15 * * * * 0", config.entities[4].destinations.planned_notifications[0].cron_expression)
        self.assertEqual("daily-appointments", config.entities[4].destinations.planned_notifications[0].subject)
        # calendar category colors
        self.assertEqual("Special", config.calendars_config.categories[0].name)
        self.assertEqual("ffff00", config.calendars_config.categories[0].color_hex)
        self.assertEqual("Important", config.calendars_config.categories[1].name)
        self.assertEqual("ff0000", config.calendars_config.categories[1].color_hex)

    def test_min_config(self):
        min_config = ConfigurationManager().load(DIR / "min_test_config.yaml")
        self.assertEqual("mqtt.local", min_config.mqtt.url)
        self.assertIsNotNone(min_config.mqtt.port)
        self.assertFalse(min_config.mqtt.has_credentials)
        self.assertIsNotNone(min_config.mqtt.client_id)

        self.assertEqual("super_washer", min_config.entities[0].name)
        self.assertEqual("washing_machine", min_config.entities[0].type)
        self.assertFalse(min_config.entities[0].sources.list)
        self.assertFalse(min_config.entities[0].destinations.planned_notifications)

        self.assertEqual("Dining room", min_config.entities[1].name)
        self.assertEqual("room", min_config.entities[1].type)
        self.assertFalse(min_config.entities[1].sources.list)
        self.assertFalse(min_config.entities[1].destinations.planned_notifications)

    def test_incomplete_sources_produce_errors(self):
        with self.subTest("incomplete loading source"):
            self.assertRaises(IncompleteConfiguration,
                              ConfigurationManager().load,
                              (DIR / "incomplete_loading_source_config.yaml"))
        with self.subTest("incomplete unloading source"):
            self.assertRaises(IncompleteConfiguration,
                              ConfigurationManager().load,
                              (DIR / "incomplete_unloading_source_config.yaml"))
        with self.subTest("incomplete mqtt conf"):
            self.assertRaises(IncompleteConfiguration,
                              ConfigurationManager().load, (DIR / "incomplete_mqtt_config.yaml"))
        with self.subTest("incomplete entity conf"):
            self.assertRaises(IncompleteConfiguration,
                              ConfigurationManager().load, (DIR / "incomplete_entity_config.yaml"))
        with self.subTest("incomplete influxdb conf"):
            self.assertRaises(IncompleteConfiguration,
                              ConfigurationManager().load, (DIR / "incomplete_influxdb_config.yaml"))
        with self.subTest("incomplete person conf"):
            self.assertRaises(IncompleteConfiguration,
                              ConfigurationManager().load,
                              (DIR / "incomplete_person_calendar_config.yaml"))

    def test_saving_config(self):
        self.maxDiff = None
        try:
            # given
            manager = ConfigurationManager()
            config = manager.load(DIR / "complete_test_config.yaml")
            dict_of_loaded_config = yamlenv.load(open(DIR / "complete_test_config.yaml"))
            # fix colors that are lower-cased internally and, therefore, saved lower too
            caldav_calendar_with_upper_case_color = dict_of_loaded_config['calendars']['caldav'][0]
            caldav_calendar_with_upper_case_color['color_hex'] = caldav_calendar_with_upper_case_color[
                'color_hex'].lower()
            # add color that is set to default
            calendar_without_color = list(filter(lambda cal: cal['name'] == 'jane private' if 'name' in cal else False,
                                                 list(filter(lambda t: t['name'] == 'Jane',
                                                             dict_of_loaded_config['entities']))[0][
                                                     'sources']))[0]
            calendar_without_color['color_hex'] = 'ffffff'
            # when
            manager.config_path = DIR / "test_result_complete_test_config.yaml"
            manager.configuration = config
            manager.save()
            # then
            self.assertEqual(dict_of_loaded_config,
                             yamlenv.load(open(DIR / "test_result_complete_test_config.yaml")))
        finally:
            os.remove(DIR / "test_result_complete_test_config.yaml")


if __name__ == '__main__':
    unittest.main()
