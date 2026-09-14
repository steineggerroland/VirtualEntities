import unittest
import yaml

from iot.core.configuration import IncompleteConfiguration
from iot.core.configuration_manager import _read_configuration


class BoardConfigurationTest(unittest.TestCase):
    def config(self):
        return {'mqtt': {'url': 'localhost'}, 'entities': [{'name': 'Person1', 'type': 'person'}],
                'calendar_boards': [{'id': 'board', 'rows': [{'id': 'person1', 'person': 'Person1'}]}]}

    def test_roundtrip_preserves_board_and_source_timezone(self):
        raw = self.config()
        raw['calendars'] = {'timezone': 'UTC'}
        raw['calendar_boards'][0]['timezone'] = 'America/New_York'
        raw['calendar_boards'][0]['night_mode'] = {'start': '22:15', 'end': '06:30'}
        config = _read_configuration(raw)
        restored = _read_configuration(yaml.safe_load(yaml.safe_dump(config)))
        self.assertEqual(config.calendar_boards, restored.calendar_boards)
        self.assertEqual('UTC', restored.calendars_config.timezone)
        self.assertTrue(restored.calendar_boards[0].night_mode.is_active_at(restored.calendar_boards[0].night_mode.start))

    def test_unknown_person_and_unsafe_topic_id_are_rejected(self):
        for key, value in [('id', 'bad/#'), ('person', 'missing')]:
            raw = self.config()
            raw['calendar_boards'][0]['rows'][0][key] = value
            with self.assertRaises(IncompleteConfiguration):
                _read_configuration(raw)

    def test_default_and_duplicate_rows(self):
        raw = self.config()
        self.assertEqual('Europe/Berlin', _read_configuration(raw).calendar_boards[0].timezone)
        raw['calendar_boards'][0]['rows'] *= 2
        with self.assertRaises(IncompleteConfiguration):
            _read_configuration(raw)

    def test_night_mode_requires_two_valid_different_times(self):
        for value in [{}, {'start': '22:00'}, {'start': '22:00', 'end': '22:00'},
                      {'start': '24:00', 'end': '06:00'}, {'start': '22:0', 'end': '06:00'}, []]:
            raw = self.config()
            raw['calendar_boards'][0]['night_mode'] = value
            with self.assertRaises(IncompleteConfiguration):
                _read_configuration(raw)
