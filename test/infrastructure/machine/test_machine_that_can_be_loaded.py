import unittest
from datetime import datetime, timedelta

from iot.infrastructure.machine.iot_machine import OnlineStatus
from iot.infrastructure.machine.machine_that_can_be_loaded import MachineThatCanBeLoaded
from iot.infrastructure.machine.power_state_decorator import PowerState


class InitTest(unittest.TestCase):
    def test_name(self):
        power_state_machine = MachineThatCanBeLoaded('super_power_state_machine')
        self.assertEqual(power_state_machine.name, 'super_power_state_machine')

    def test_unknown_watt(self):
        power_state_machine = MachineThatCanBeLoaded('power_state_machine')
        self.assertEqual(power_state_machine.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        power_state_machine = MachineThatCanBeLoaded('power_state_machine', 0)
        self.assertEqual(power_state_machine.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        power_state_machine = MachineThatCanBeLoaded('power_state_machine', 4)
        self.assertEqual(power_state_machine.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        power_state_machine = MachineThatCanBeLoaded('power_state_machine', 400)
        self.assertEqual(power_state_machine.power_state, PowerState.RUNNING)


class MachineThatCanBeLoadedTest(unittest.TestCase):
    def setUp(self):
        self.machine = MachineThatCanBeLoaded('my-power_state_machine', 0)

    def test_start_run(self):
        # given
        self.machine.update_power_consumption(2000)
        # when
        self.machine.start_run()
        # then
        self.assertAlmostEqual(self.machine.started_run_at, datetime.now(), delta=timedelta(milliseconds=100))
        self.assertTrue(self.machine.is_loaded)
        self.assertFalse(self.machine.needs_unloading)

    def test_finish_run(self):
        # given
        self.machine.is_loaded = True
        self.machine.power_state = PowerState.RUNNING
        # when
        self.machine.finish_run()
        # then
        self.assertAlmostEqual(self.machine.finished_last_run_at, datetime.now(), delta=timedelta(milliseconds=100))
        self.assertIsNone(self.machine.started_run_at)
        self.assertTrue(self.machine.is_loaded)
        self.assertTrue(self.machine.needs_unloading)

    def test_loading_machine(self):
        # given
        self.machine.is_loaded = self.machine.needs_unloading = False
        # when
        self.machine.load()
        # then
        self.assertTrue(self.machine.is_loaded)

    def test_unloading_machine(self):
        # given
        self.machine.is_loaded = self.machine.needs_unloading = True
        # when
        self.machine.unload()
        # then
        self.assertFalse(self.machine.is_loaded)
        self.assertFalse(self.machine.needs_unloading)

    def test_not_online_when_un_loading(self):
        # given
        self.machine.last_seen_at = None
        # when
        self.machine.load()
        self.machine.unload()
        # then
        self.assertNotEqual(self.machine.online_status(), OnlineStatus.ONLINE)

    def test_not_online_when_starting_or_finishing(self):
        # given
        self.machine.last_seen_at = None
        # when
        self.machine.start_run()
        self.machine.finish_run()
        # then
        self.assertNotEqual(self.machine.online_status(), OnlineStatus.ONLINE)

    def test_to_dict_has_mandatory_fields(self):
        last_updated_at = datetime.now()
        last_seen_at = datetime.now() - timedelta(seconds=5)
        power_state_machine = MachineThatCanBeLoaded("test", 312.5, last_updated_at=last_updated_at,
                                                     last_seen_at=last_seen_at)
        self.assertDictEqual(power_state_machine.to_dict(),
                             {"name": "test", "watt": 312.5, "power_state": PowerState.RUNNING,
                              "needs_unloading": False, "is_loaded": False,
                              "started_run_at": None, "finished_last_run_at": None,
                              "online_status": OnlineStatus.ONLINE, "last_updated_at": last_updated_at.isoformat(),
                              "last_seen_at": last_seen_at.isoformat()})


if __name__ == '__main__':
    unittest.main()
