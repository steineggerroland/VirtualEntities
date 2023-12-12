import unittest
from datetime import datetime, timedelta

from iot.infrastructure.machine.IotMachine import OnlineStatus
from iot.infrastructure.machine.PowerStateDecorator import PowerState
from iot.infrastructure.machine.WashingMachine import from_dict


class WashingMachineInitTest(unittest.TestCase):
    def test_minimal_dict(self):
        name = "my super washing_machine"
        washing_machine = from_dict({"name": name})
        self.assertEqual(washing_machine.name, name)
        self.assertEqual(washing_machine.started_run_at, None)
        self.assertEqual(washing_machine.finished_last_run_at, None)
        self.assertEqual(washing_machine.is_loaded, False)
        self.assertEqual(washing_machine.needs_unloading, False)
        self.assertEqual(washing_machine.power_state, PowerState.UNKNOWN)
        self.assertEqual(washing_machine.watt, None)
        self.assertEqual(washing_machine.online_status(), OnlineStatus.UNKNOWN)
        self.assertEqual(washing_machine.last_updated_at, None)

    def test_complete_dict(self):
        last_updated_at = datetime.now()
        started_run_at = datetime.now()
        finished_last_run_at = datetime.now()
        last_seen_at = datetime.now() - timedelta(seconds=5)
        name = 'my super washing_machine'
        watt = 255
        is_loaded = True
        needs_unloading = False
        washing_machine = from_dict(
            {'name': name, 'watt': watt, 'last_updated_at': last_updated_at.isoformat(),
             'started_run_at': started_run_at.isoformat(), 'finished_last_run_at': finished_last_run_at.isoformat(),
             'is_loaded': is_loaded, 'needs_unloading': needs_unloading, "last_seen_at": last_seen_at.isoformat()})
        self.assertEqual(washing_machine.name, name)
        self.assertEqual(washing_machine.started_run_at, started_run_at)
        self.assertEqual(washing_machine.is_loaded, is_loaded)
        self.assertEqual(washing_machine.needs_unloading, needs_unloading)
        self.assertEqual(washing_machine.power_state, PowerState.RUNNING)
        self.assertEqual(washing_machine.watt, watt)
        self.assertEqual(washing_machine.online_status(), OnlineStatus.ONLINE)
        self.assertEqual(washing_machine.last_updated_at, last_updated_at)
        self.assertEqual(washing_machine.finished_last_run_at, finished_last_run_at)


if __name__ == '__main__':
    unittest.main()
