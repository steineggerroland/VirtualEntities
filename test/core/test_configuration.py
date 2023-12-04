import unittest

from iot.core import configuration


class ConfigurationTest(unittest.TestCase):
    def test_complete_config(self):
        config = configuration.load_configuration("complete_test_config.yaml")
        self.assertEqual(config.name, "super_thing")
        self.assertEqual(config.type, "dryer")

        self.assertEqual(config.mqtt.url, "my.machine.local")
        self.assertEqual(config.mqtt.port, 1337)
        self.assertTrue(config.mqtt.has_credentials)
        self.assertEqual(config.mqtt.username, "user")
        self.assertEqual(config.mqtt.password, "my-secret")
        self.assertEqual(config.mqtt.client_id, "my-client")

        self.assertEqual(config.sources.consumption_topic, "consumption/topic")

    def test_min_config(self):
        min_config = configuration.load_configuration("min_test_config.yaml")
        self.assertEqual(min_config.name, "super_washer")
        self.assertEqual(min_config.type, "washing_machine")

        self.assertEqual(min_config.mqtt.url, "mqtt.local")
        self.assertIsNotNone(min_config.mqtt.port)
        self.assertFalse(min_config.mqtt.has_credentials)
        self.assertIsNotNone(min_config.mqtt.client_id)

        self.assertEqual(min_config.sources.consumption_topic, "washer/consumption/topic")


if __name__ == '__main__':
    unittest.main()
