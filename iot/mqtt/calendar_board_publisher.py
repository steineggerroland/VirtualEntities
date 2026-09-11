"""Publish bounded day snapshots and fresh time without doing I/O in MQTT callbacks."""
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from threading import Event, Thread
from zoneinfo import ZoneInfo

from iot.infrastructure.time.day_view import project_day


def utc_text(value):
    return value.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


class CalendarBoardPublisher:
    def __init__(self, mqtt_client, config, person_services, clock=None):
        self.mqtt = mqtt_client
        self.config = config
        self.zone = ZoneInfo(config.timezone)
        self.rows = [(row.id, person_services[row.person]) for row in config.rows]
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.base = f'calendarboard/v1/{config.id}'
        self.logger = logging.getLogger(__name__)
        self._stop = Event()
        self._sync = Event()
        self._sync.set()
        self._last_sent = {}
        self._last_complete = {}
        self._pending = {}
        self._last_time_sent = None
        self._thread = Thread(target=self._run, daemon=True)
        self.mqtt.subscribe(self.base, self.base + '/sync/request', self._request)
        self.mqtt.add_connected_callback(self._sync.set)

    def _request(self, message):
        # Retained requests must not cause repeated unsolicited resynchronization.
        if message.retain or len(message.payload) > 128:
            return
        try:
            payload = json.loads(message.payload)
        except (ValueError, TypeError):
            return
        if isinstance(payload, dict) and type(payload.get('schema_version')) is int and payload['schema_version'] == 1:
            self._sync.set()

    def start(self):
        self._thread.start()

    def shutdown(self, timeout=2):
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout)
        self.mqtt.unsubscribe(self.base)
        self.mqtt.remove_connected_callback(self._sync.set)

    def _run(self):
        while not self._stop.is_set():
            self.tick()
            self._stop.wait(1)

    def _publish(self, suffix, payload, retained):
        encoded = json.dumps(payload, separators=(',', ':'), ensure_ascii=True)
        topic = self.base + '/' + suffix
        if len(encoded.encode('utf-8')) > 768 or len(topic.encode('utf-8')) > 96:
            raise ValueError('Board message exceeds protocol limits')
        if not self.mqtt.is_connected():
            raise ConnectionError('MQTT disconnected')
        pending = self._pending.get(topic)
        if pending:
            previous_payload, previous_result = pending
            previous_result.wait_for_publish(timeout=2)
            if not previous_result.is_published():
                raise ConnectionError('Previous MQTT snapshot still awaiting acknowledgement')
            del self._pending[topic]
            if previous_payload == encoded:
                return
        result = self.mqtt.publish(topic, encoded, qos=1 if retained else 0, retain=retained)
        if result.rc != 0:
            raise ConnectionError('MQTT publish rejected')
        if retained:
            self._pending[topic] = (encoded, result)
            result.wait_for_publish(timeout=2)
            if not result.is_published():
                raise ConnectionError('MQTT snapshot not acknowledged')
            del self._pending[topic]

    def _snapshot(self, row_id, service, now):
        day = now.astimezone(self.zone).date()
        calendars, errors = service.calendar_snapshot()
        complete = bool(calendars) and all(
            calendar.last_seen_at is not None and calendar.loaded_from is not None
            and calendar.loaded_until is not None and calendar.loaded_from <= day < calendar.loaded_until
            for calendar in calendars)
        checked = min((calendar.last_seen_at for calendar in calendars if calendar.last_seen_at), default=None)
        fresh = complete and not errors and all(
            timedelta(0) <= now - calendar.last_seen_at <= timedelta(minutes=30) for calendar in calendars)
        previous = self._last_complete.get(row_id)
        if fresh:
            slots = project_day((appointment for calendar in calendars for appointment in calendar.appointments),
                                day, self.config.timezone)
            self._last_complete[row_id] = (day, slots, checked)
            status = 'ok'
        elif previous and previous[0] == day:
            _, slots, checked = previous
            status = 'stale'
        else:
            slots, status = None, 'unavailable'
        return {'schema_version': 1, 'date': day.isoformat(), 'timezone': self.config.timezone,
                'generated_at': utc_text(now), 'source_checked_at': utc_text(checked) if checked else None,
                'status': status, 'slots': slots}

    def tick(self):
        """One serialized worker step; injectable time keeps protocol tests deterministic."""
        force = self._sync.is_set()
        self._sync.clear()
        now = self.clock()
        monotonic_now = time.monotonic()
        if force or self._last_time_sent is None or monotonic_now - self._last_time_sent >= 30:
            try:
                self._publish('time', {'schema_version': 1, 'utc': utc_text(now),
                                      'local': now.astimezone(self.zone).isoformat(timespec='seconds'),
                                      'timezone': self.config.timezone}, False)
                self._last_time_sent = monotonic_now
            except Exception:
                self.logger.exception('Board time publish failed for %s', self.config.id)
        for row_id, service in self.rows:
            if self._stop.is_set():
                break
            try:
                payload = self._snapshot(row_id, service, now)
                # Source polling timestamps alone must not generate network traffic.
                fingerprint = (payload['date'], payload['status'], payload['slots'])
                if force or self._last_sent.get(row_id) != fingerprint:
                    self._publish(f'rows/{row_id}/day', payload, True)
                    self._last_sent[row_id] = fingerprint
            except Exception:
                self.logger.exception('Board snapshot publish failed for %s/%s', self.config.id, row_id)
