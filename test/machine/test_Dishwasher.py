import datetime
import unittest

from iot.machine.Dishwasher import from_dict
from iot.machine.IotMachine import OnlineStatus
from iot.machine.PowerStateDecorator import PowerState


class WashingMachineInitTest(unittest.TestCase):
    def test_minimal_dict(self):
        name = "my super dishwasher"
        dishwasher = from_dict({"name": name})
        self.assertEqual(dishwasher.name, name)
        self.assertEqual(dishwasher.started_run_at, None)
        self.assertEqual(dishwasher.finished_last_run_at, None)
        self.assertEqual(dishwasher.is_loaded, False)
        self.assertEqual(dishwasher.needs_unloading, False)
        self.assertEqual(dishwasher.power_state, PowerState.UNKNOWN)
        self.assertEqual(dishwasher.watt, None)
        self.assertEqual(dishwasher.online_status(), OnlineStatus.UNKNOWN)
        self.assertEqual(dishwasher.last_updated_at, None)

    def test_complete_dict(self):
        last_updated_at = datetime.datetime.now()
        started_run_at = datetime.datetime.now()
        finished_last_run_at = datetime.datetime.now()
        dict = {'name': 'my super dishwasher', 'watt': 255, 'last_updated_at': last_updated_at.isoformat(),
                'started_run_at': started_run_at.isoformat(), 'finished_last_run_at': finished_last_run_at.isoformat(),
                'is_loaded': True, 'needs_unloading': False}
        dishwasher = from_dict(dict)
        self.assertEqual(dishwasher.name, dict['name'])
        self.assertEqual(dishwasher.started_run_at, started_run_at)
        self.assertEqual(dishwasher.is_loaded, True)
        self.assertEqual(dishwasher.needs_unloading, False)
        self.assertEqual(dishwasher.power_state, PowerState.RUNNING)
        self.assertEqual(dishwasher.watt, dict['watt'])
        self.assertEqual(dishwasher.online_status(), OnlineStatus.ONLINE)
        self.assertEqual(dishwasher.last_updated_at, last_updated_at)
        self.assertEqual(dishwasher.finished_last_run_at, finished_last_run_at)


if __name__ == '__main__':
    unittest.main()
