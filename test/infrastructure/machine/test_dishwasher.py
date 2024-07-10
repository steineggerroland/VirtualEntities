import unittest
from datetime import datetime, timedelta

from iot.infrastructure.appliance.dishwasher import from_dict
from iot.infrastructure.appliance.machine_that_can_be_loaded import RunningState
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.virtual_entity import OnlineStatus


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
        last_updated_at = datetime.now()
        started_run_at = datetime.now()
        running_state = RunningState.IDLE
        finished_last_run_at = datetime.now()
        last_seen_at = datetime.now() - timedelta(seconds=5)
        name = 'my super washing_machine'
        watt = 255
        is_loaded = True
        needs_unloading = False
        washing_machine = from_dict(
            {'name': name, "type": "washing_machine", 'watt': watt, 'last_updated_at': last_updated_at.isoformat(),
             'started_run_at': started_run_at.isoformat(), 'running_state': running_state,
             'finished_last_run_at': finished_last_run_at.isoformat(), 'is_loaded': is_loaded,
             'needs_unloading': needs_unloading, "last_seen_at": last_seen_at.isoformat()})
        self.assertEqual(washing_machine.name, name)
        self.assertEqual(washing_machine.is_loaded, is_loaded)
        self.assertEqual(washing_machine.needs_unloading, needs_unloading)
        self.assertEqual(washing_machine.power_state, PowerState.RUNNING)
        self.assertEqual(washing_machine.watt, watt)
        self.assertEqual(washing_machine.online_status(), OnlineStatus.ONLINE)
        self.assertEqual(washing_machine.last_updated_at, last_updated_at)
        self.assertEqual(washing_machine.started_run_at, started_run_at)
        self.assertEqual(washing_machine.running_state, running_state)
        self.assertEqual(washing_machine.finished_last_run_at, finished_last_run_at)


if __name__ == '__main__':
    unittest.main()
