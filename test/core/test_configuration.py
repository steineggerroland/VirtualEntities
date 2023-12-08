import unittest
from pathlib import Path

from iot.core import configuration
from iot.core.configuration import PlannedNotification, IncompleteConfiguration

DIR = Path(__file__).parent


class ConfigurationTest(unittest.TestCase):
    def test_complete_config(self):
        config = configuration.load_configuration(DIR / "complete_test_config.yaml")
        self.assertEqual(config.name, "super_thing")
        self.assertEqual(config.type, "dryer")

        self.assertEqual(config.mqtt.url, "my.machine.local")
        self.assertEqual(config.mqtt.port, 1337)
        self.assertTrue(config.mqtt.has_credentials)
        self.assertEqual(config.mqtt.username, "user")
        self.assertEqual(config.mqtt.password, "my-secret")
        self.assertEqual(config.mqtt.client_id, "my-client")

        self.assertEqual(config.sources.consumption_topic, "consumption/topic")
        self.assertEqual(config.sources.loading_topic, "loading/topic")
        self.assertEqual(config.sources.unloading_topic, "unloading/topic")

        self.assertIn(PlannedNotification('update/every-second/topic', '*/1 * * * * *'),
                      config.destinations.planned_notifications)
        self.assertIn(PlannedNotification('update/every-15-minutes/topic', '* */15 * * * *'),
                      config.destinations.planned_notifications)

    def test_min_config(self):
        min_config = configuration.load_configuration(DIR / "min_test_config.yaml")
        self.assertEqual(min_config.name, "super_washer")
        self.assertEqual(min_config.type, "washing_machine")

        self.assertEqual(min_config.mqtt.url, "mqtt.local")
        self.assertIsNotNone(min_config.mqtt.port)
        self.assertFalse(min_config.mqtt.has_credentials)
        self.assertIsNotNone(min_config.mqtt.client_id)

        self.assertEqual(min_config.sources.consumption_topic, "washer/consumption/topic")
        self.assertIsNone(min_config.sources.loading_topic)
        self.assertIsNone(min_config.sources.unloading_topic)

        self.assertTrue(len(min_config.destinations.planned_notifications) == 0)

    def test_incomplete_sources_produce_errors(self):
        self.assertRaises(IncompleteConfiguration,
                          configuration.load_configuration, (DIR / "incomplete_loading_source_config.yaml"))
        self.assertRaises(IncompleteConfiguration,
                          configuration.load_configuration, (DIR / "incomplete_unloading_source_config.yaml"))
        self.assertRaises(IncompleteConfiguration,
                          configuration.load_configuration, (DIR / "incomplete_mqtt_config.yaml"))
        self.assertRaises(IncompleteConfiguration,
                          configuration.load_configuration, (DIR / "incomplete_thing_config.yaml"))


if __name__ == '__main__':
    unittest.main()
