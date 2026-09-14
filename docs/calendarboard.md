# CalendarBoard v1

The board publisher is opt-in. Existing installations without `calendar_boards`
keep their legacy MQTT destinations. The new publisher runs alongside them on
separate topics; remove the old daily notification only after firmware migration.

Add this section to the application YAML. `person` must exactly match an existing
person name. Row IDs are stable and remain unchanged when a person is renamed
through the application. The firmware maps them to physical rows in this order.

```yaml
calendar_boards:
  - id: example-board
    timezone: Europe/Berlin
    night_mode:
      start: "22:00"
      end: "06:00"
    rows:
      - {id: person1, person: person1}
      - {id: person2, person: person2}
      - {id: person3, person: person3}
      - {id: person4, person: person4}
```

`calendars.timezone` optionally sets the source timezone for floating timestamps
and the CalDAV download window. Its default is `Europe/Berlin`, independently of
the host timezone. Each board can select its own display timezone. Currently all
calendars of the selected person contribute to a row.

## Messages

Topics are under `calendarboard/v1/{board_id}`. Board and row IDs must contain
1–32 ASCII letters, digits, underscores or hyphens.

- `time`: non-retained QoS 0, every 30 seconds and on synchronization. Fields:
  `schema_version: 1`, `utc` (ISO UTC ending in Z), `local` (ISO including offset),
  `timezone` (IANA name). Date and time are one atomic observation.
- `rows/{row_id}/day`: retained QoS 1, acknowledged before considering delivery
  successful. Fields: `schema_version: 1`, local `date`, `timezone`,
  `generated_at`, `source_checked_at`, `status`, `all_day`, `slots`.
- `sync/request`: non-retained request `{"schema_version":1}` from the board on
  boot, reconnect or date change. Replies contain fresh time and all current rows.
  Only the current day view is supported. Retained and malformed requests are ignored.

A day has 24 slots, each null, `ffffff` (ordinary appointment) or `ff0000`
(title starts exactly with `Wichtig:`). Red wins overlaps. `all_day` is null,
`ffffff` or `ff0000` and controls the 25th LED of the row. All-day events do not
occupy hourly slots. Spring's missing hour remains empty; autumn's repeated hour
shares one slot. Physical LED positions and night mode are firmware responsibilities.

`night_mode` is optional. If configured, `start` and `end` are local board times
in strict `HH:MM` notation and must differ. The interval can cross midnight. The
publisher sends `on` to `home/things/{board_id}/nightmode` at the start, `off` at
the end, and the current value for every board synchronization request.

A complete successful import with no appointments produces 24 nulls and `ok`.
A failed or more than 30-minute-old source uses the last complete projection of
that same day as `stale`. Without that cached projection the status is
`unavailable` and slots is null. Firmware should keep its previous display when
new data is unavailable; a disconnected board should continue its local clock.
A restarted publisher cannot reconstruct a previously cached stale projection.
It awaits complete fresh imports while the board retains its last display.

The worker checks in-memory data once per second, but transmits only when date,
slots or status changes, or when explicitly synchronized. A successful source
poll alone does not trigger traffic. Snapshot payloads are capped at 768 UTF-8
bytes and topics at 96 bytes. Publish failures are retried by subsequent worker
steps. Time is never retained. Exactly one publisher should own a board ID.

Removed rows leave retained messages on the broker: until an explicit retirement
mechanism is implemented, clear these administratively during reconfiguration.
No live board configuration or broker changes are performed by this implementation.

## Verification

Run `python -m unittest discover -s test` in an environment containing
`requirements.txt`. Unit tests use a mocked MQTT client and fixed dates. A live
broker and firmware/hardware end-to-end test remains necessary before migration.
