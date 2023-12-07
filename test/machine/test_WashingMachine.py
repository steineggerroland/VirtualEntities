import datetime
import unittest

from iot.machine.WashingMachine import from_dict
from iot.machine.IotMachine import OnlineStatus
from iot.machine.PowerStateDecorator import PowerState


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
        last_updated_at = datetime.datetime.now()
        started_run_at = datetime.datetime.now()
        finished_last_run_at = datetime.datetime.now()
        dict = {'name': 'my super washing_machine', 'watt': 255, 'last_updated_at': last_updated_at.isoformat(),
                'started_run_at': started_run_at.isoformat(), 'finished_last_run_at': finished_last_run_at.isoformat(),
                'is_loaded': True, 'needs_unloading': False}
        washing_machine = from_dict(dict)
        self.assertEqual(washing_machine.name, dict['name'])
        self.assertEqual(washing_machine.started_run_at, started_run_at)
        self.assertEqual(washing_machine.is_loaded, True)
        self.assertEqual(washing_machine.needs_unloading, False)
        self.assertEqual(washing_machine.power_state, PowerState.RUNNING)
        self.assertEqual(washing_machine.watt, dict['watt'])
        self.assertEqual(washing_machine.online_status(), OnlineStatus.ONLINE)
        self.assertEqual(washing_machine.last_updated_at, last_updated_at)
        self.assertEqual(washing_machine.finished_last_run_at, finished_last_run_at)


if __name__ == '__main__':
    unittest.main()
