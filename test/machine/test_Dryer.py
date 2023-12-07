import datetime
import unittest

from iot.machine.Dryer import from_dict
from iot.machine.IotMachine import OnlineStatus
from iot.machine.PowerStateDecorator import PowerState


class DryerInitTest(unittest.TestCase):
    def test_minimal_dict(self):
        name = "my super dryer"
        dryer = from_dict({"name": name})
        self.assertEqual(dryer.name, name)
        self.assertEqual(dryer.started_run_at, None)
        self.assertEqual(dryer.finished_last_run_at, None)
        self.assertEqual(dryer.is_loaded, False)
        self.assertEqual(dryer.needs_unloading, False)
        self.assertEqual(dryer.power_state, PowerState.UNKNOWN)
        self.assertEqual(dryer.watt, None)
        self.assertEqual(dryer.online_status(), OnlineStatus.UNKNOWN)
        self.assertEqual(dryer.last_updated_at, None)

    def test_complete_dict(self):
        last_updated_at = datetime.datetime.now()
        started_run_at = datetime.datetime.now()
        finished_last_run_at = datetime.datetime.now()
        dict = {'name': 'my super dryer', 'watt': 255, 'last_updated_at': last_updated_at.isoformat(),
                'started_run_at': started_run_at.isoformat(), 'finished_last_run_at': finished_last_run_at.isoformat(),
                'is_loaded': True, 'needs_unloading': False}
        dryer = from_dict(dict)
        self.assertEqual(dryer.name, dict['name'])
        self.assertEqual(dryer.started_run_at, started_run_at)
        self.assertEqual(dryer.is_loaded, True)
        self.assertEqual(dryer.needs_unloading, False)
        self.assertEqual(dryer.power_state, PowerState.RUNNING)
        self.assertEqual(dryer.watt, dict['watt'])
        self.assertEqual(dryer.online_status(), OnlineStatus.ONLINE)
        self.assertEqual(dryer.last_updated_at, last_updated_at)
        self.assertEqual(dryer.finished_last_run_at, finished_last_run_at)


if __name__ == '__main__':
    unittest.main()
