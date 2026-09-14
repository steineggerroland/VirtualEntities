import json
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock

from iot.core.configuration import CalendarBoardConfig, BoardRowConfig, NightModeConfig
from iot.infrastructure.time.calendar import Calendar, Appointment
from iot.mqtt.calendar_board_publisher import CalendarBoardPublisher


class BoardPublisherTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)
        self.calendar = Calendar('a', '', '', last_seen_at=self.now,
                                 loaded_from=date(2026, 9, 11), loaded_until=date(2026, 9, 18))
        self.service = Mock()
        self.service.calendar_snapshot.return_value = ((self.calendar,), frozenset())
        self.mqtt = Mock()
        self.mqtt.publish.return_value = Mock(rc=0, is_published=Mock(return_value=True))
        config = CalendarBoardConfig('board', (BoardRowConfig('person1', 'Person1'),))
        self.publisher = CalendarBoardPublisher(self.mqtt, config, {'Person1': self.service}, lambda: self.now)

    def messages(self):
        return [(call.args[0], json.loads(call.args[1]), call.kwargs) for call in self.mqtt.publish.call_args_list]

    def night_mode_messages(self):
        return [call for call in self.mqtt.publish.call_args_list if call.args[0].endswith('/nightmode')]

    def test_start_and_no_traffic_for_unchanged_poll(self):
        self.publisher.tick()
        self.assertEqual(2, len(self.messages()))
        self.assertFalse(self.messages()[0][2]['retain'])
        self.assertEqual('2026-09-11T14:00:00+02:00', self.messages()[0][1]['local'])
        self.assertEqual([None] * 24, self.messages()[1][1]['slots'])
        self.assertIsNone(self.messages()[1][1]['all_day'])
        self.assertEqual({'qos': 1, 'retain': True}, self.messages()[1][2])
        self.calendar.last_seen_at += timedelta(seconds=1)
        self.now += timedelta(seconds=1)
        self.publisher.tick()
        self.assertEqual(2, len(self.messages()))

    def test_changes_and_sync_republish(self):
        self.publisher.tick()
        self.calendar.appointments = [Appointment('Wichtig: Termin', self.now, self.now + timedelta(minutes=20), '')]
        self.publisher.tick()
        self.assertEqual('ff0000', self.messages()[-1][1]['slots'][14])
        self.publisher._request(Mock(retain=False, payload=b'{"schema_version":1}'))
        self.publisher.tick()
        self.assertEqual(5, len(self.messages()))

    def test_night_mode_is_published_at_transitions_and_on_sync(self):
        config = CalendarBoardConfig('board', (BoardRowConfig('person1', 'Person1'),),
                                     night_mode=NightModeConfig(datetime.strptime('22:00', '%H:%M').time(),
                                                                datetime.strptime('06:00', '%H:%M').time()))
        publisher = CalendarBoardPublisher(self.mqtt, config, {'Person1': self.service}, lambda: self.now)
        publisher.tick()
        self.assertEqual(('home/things/board/nightmode', 'off'),
                         (self.night_mode_messages()[0].args[0], self.night_mode_messages()[0].args[1]))
        self.assertEqual({'qos': 1, 'retain': False}, self.night_mode_messages()[0].kwargs)
        self.now = datetime(2026, 9, 11, 21, tzinfo=timezone.utc)  # 23:00 in Berlin
        publisher.tick()
        self.assertEqual(('home/things/board/nightmode', 'on'),
                         (self.night_mode_messages()[-1].args[0], self.night_mode_messages()[-1].args[1]))
        publisher._request(Mock(retain=False, payload=b'{"schema_version":1}'))
        publisher.tick()
        self.assertEqual(('home/things/board/nightmode', 'on'),
                         (self.night_mode_messages()[-1].args[0], self.night_mode_messages()[-1].args[1]))
        self.now = datetime(2026, 9, 12, 5, tzinfo=timezone.utc)  # 07:00 in Berlin
        publisher.tick()
        self.assertEqual(('home/things/board/nightmode', 'off'),
                         (self.night_mode_messages()[-1].args[0], self.night_mode_messages()[-1].args[1]))

    def test_all_day_event_updates_indicator_without_filling_hours(self):
        self.calendar.appointments = [Appointment('Wichtig: Urlaub', date(2026, 9, 11), date(2026, 9, 12), '')]
        self.publisher.tick()
        payload = self.messages()[-1][1]
        self.assertEqual('ff0000', payload['all_day'])
        self.assertEqual([None] * 24, payload['slots'])

    def test_failed_import_retains_last_complete_then_recovers(self):
        self.publisher.tick()
        self.service.calendar_snapshot.return_value = ((self.calendar,), frozenset({'a'}))
        self.publisher.tick()
        self.assertEqual('stale', self.messages()[-1][1]['status'])
        self.service.calendar_snapshot.return_value = ((self.calendar,), frozenset())
        self.publisher.tick()
        self.assertEqual('ok', self.messages()[-1][1]['status'])

    def test_first_load_is_not_confused_with_empty_calendar(self):
        self.service.calendar_snapshot.return_value = ((Calendar('a', '', ''),), frozenset())
        self.publisher.tick()
        self.assertEqual('unavailable', self.messages()[-1][1]['status'])
        self.assertIsNone(self.messages()[-1][1]['slots'])

    def test_midnight_produces_new_date_without_calendar_change(self):
        self.publisher.tick()
        self.now = datetime(2026, 9, 11, 22, tzinfo=timezone.utc)
        self.calendar.last_seen_at = self.now
        self.publisher.tick()
        self.assertEqual('2026-09-12', self.messages()[-1][1]['date'])

    def test_failed_publish_is_retried(self):
        self.mqtt.publish.return_value.rc = 1
        with self.assertLogs('iot.mqtt.calendar_board_publisher', level='ERROR'):
            self.publisher.tick()
        self.mqtt.publish.return_value.rc = 0
        self.publisher.tick()
        self.assertEqual(4, len(self.messages()))

    def test_reconnect_forces_resend(self):
        self.publisher.tick()
        self.mqtt.add_connected_callback.call_args.args[0]()
        self.publisher.tick()
        self.assertEqual(4, len(self.messages()))

    def test_retained_and_invalid_requests_are_ignored(self):
        self.publisher.tick()
        for payload, retained in [(b'{"schema_version":1}', True), (b'[]', False),
                                  (b'{"schema_version":true}', False), (b'invalid', False)]:
            self.publisher._request(Mock(payload=payload, retain=retained))
        self.publisher.tick()
        self.assertEqual(2, len(self.messages()))

    def test_outage_does_not_enqueue_snapshots(self):
        self.mqtt.is_connected.return_value = False
        with self.assertLogs('iot.mqtt.calendar_board_publisher', level='ERROR'):
            self.publisher.tick()
            self.publisher.tick()
        self.mqtt.publish.assert_not_called()

    def test_unacknowledged_snapshot_is_not_requeued(self):
        self.mqtt.publish.return_value.is_published.return_value = False
        with self.assertLogs('iot.mqtt.calendar_board_publisher', level='ERROR'):
            self.publisher.tick()
            self.publisher.tick()
        self.assertEqual(2, len(self.messages()))

    def test_full_snapshot_stays_inside_packet_budget(self):
        self.calendar.appointments = [Appointment('Wichtig: Tag',
            datetime(2026, 9, 11, 0, tzinfo=timezone.utc) - timedelta(hours=2),
            datetime(2026, 9, 12, 0, tzinfo=timezone.utc), '')]
        self.publisher.tick()
        payload = self.mqtt.publish.call_args.args[1]
        self.assertLessEqual(len(payload.encode('utf-8')), 768)
        self.assertEqual(['ff0000'] * 24, json.loads(payload)['slots'])
