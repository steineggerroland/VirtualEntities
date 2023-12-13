import unittest
from pathlib import Path

from iot.core import configuration
from iot.core.configuration import PlannedNotification, IncompleteConfiguration

DIR = Path(__file__).parent


class ConfigurationTest(unittest.TestCase):
    def test_complete_config(self):
        config = configuration.load_configuration(DIR / "complete_test_config.yaml")
        self.assertEqual(config.mqtt.url, "my.machine.local")
        self.assertEqual(config.mqtt.port, 1337)
        self.assertTrue(config.mqtt.has_credentials)
        self.assertEqual(config.mqtt.username, "user")
        self.assertEqual(config.mqtt.password, "my-secret")
        self.assertEqual(config.mqtt.client_id, "my-client")

        self.assertEqual(config.things[0].name, "super_thing")
        self.assertEqual(config.things[0].type, "dryer")
        self.assertEqual(config.things[0].sources.consumption_topic, "consumption/topic")
        self.assertEqual(config.things[0].sources.loading_topic, "loading/topic")
        self.assertEqual(config.things[0].sources.unloading_topic, "unloading/topic")

        self.assertIn(PlannedNotification('update/every-second/topic', '*/1 * * * * *'),
                      config.things[0].destinations.planned_notifications)
        self.assertIn(PlannedNotification('update/every-15-minutes/topic', '* */15 * * * *'),
                      config.things[0].destinations.planned_notifications)

    def test_min_config(self):
        min_config = configuration.load_configuration(DIR / "min_test_config.yaml")
        self.assertEqual("mqtt.local", min_config.mqtt.url)
        self.assertIsNotNone(min_config.mqtt.port)
        self.assertFalse(min_config.mqtt.has_credentials)
        self.assertIsNotNone(min_config.mqtt.client_id)

        self.assertEqual("super_washer", min_config.things[0].name)
        self.assertEqual("washing_machine", min_config.things[0].type)
        self.assertEqual("washer/consumption/topic", min_config.things[0].sources.consumption_topic)
        self.assertIsNone(min_config.things[0].sources.loading_topic)
        self.assertIsNone(min_config.things[0].sources.unloading_topic)
        self.assertFalse(min_config.things[0].destinations.planned_notifications)

        self.assertEqual("Dining room", min_config.things[1].name)
        self.assertEqual("room", min_config.things[1].type)
        self.assertFalse(min_config.things[1].sources.list)
        self.assertFalse(min_config.things[1].destinations.planned_notifications)

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
