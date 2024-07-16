import unittest
from datetime import datetime, timedelta

from iot.infrastructure.appliance.appliance_that_can_be_loaded import ApplianceThatCanBeLoaded, RunningState
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.virtual_entity import OnlineStatus


class ApplianceThatCanBeLoadedInitTest(unittest.TestCase):
    def test_minimal_dict(self):
        name = "my super dishwasher"
        dishwasher = ApplianceThatCanBeLoaded.from_dict({"name": name, "type": "dishwasher"})
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
        washing_machine = ApplianceThatCanBeLoaded.from_dict(
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


class InitTest(unittest.TestCase):
    def test_name(self):
        power_state_appliance = ApplianceThatCanBeLoaded('super_power_state_appliance', "some appliance")
        self.assertEqual(power_state_appliance.name, 'super_power_state_appliance')

    def test_unknown_watt(self):
        power_state_appliance = ApplianceThatCanBeLoaded('power_state_appliance', "some appliance")
        self.assertEqual(power_state_appliance.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        power_state_appliance = ApplianceThatCanBeLoaded('power_state_appliance', "some appliance", 0)
        self.assertEqual(power_state_appliance.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        power_state_appliance = ApplianceThatCanBeLoaded('power_state_appliance', "some appliance", 4)
        self.assertEqual(power_state_appliance.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        power_state_appliance = ApplianceThatCanBeLoaded('power_state_appliance', "some appliance", 400)
        self.assertEqual(power_state_appliance.power_state, PowerState.RUNNING)


class ApplianceThatCanBeLoadedTest(unittest.TestCase):
    def setUp(self):
        self.appliance = ApplianceThatCanBeLoaded('my-power_state_appliance', "some appliance", 0)

    def test_sets_running_state_idle_when_off_after_updating_power_consumption(self):
        # given
        appliance = ApplianceThatCanBeLoaded('unknown appliance', "some appliance", running_state=RunningState.UNKNOWN)
        # when
        appliance.update_power_consumption(0)
        # then
        self.assertEqual(RunningState.IDLE, appliance.running_state)

    def test_sets_running_state_run_when_running_after_updating_power_consumption(self):
        # given
        appliance = ApplianceThatCanBeLoaded('unknown appliance', "some appliance", running_state=RunningState.UNKNOWN)
        # when
        appliance.update_power_consumption(2000)
        # then
        self.assertEqual(RunningState.RUNNING, appliance.running_state)

    def test_sets_start_at_when_starting_run(self):
        # given
        self.appliance.update_power_consumption(2000)
        # when
        self.appliance.start_run()
        # then
        self.assertAlmostEqual(self.appliance.started_run_at, datetime.now(), delta=timedelta(milliseconds=100))

    def test_sets_appliance_loaded_when_starting_run(self):
        # given
        self.appliance.update_power_consumption(2000)
        # when
        self.appliance.start_run()
        # then
        self.assertTrue(self.appliance.is_loaded)

    def test_sets_no_need_for_unload_when_starting_run(self):
        # given
        self.appliance.update_power_consumption(2000)
        # when
        self.appliance.start_run()
        # then
        self.assertFalse(self.appliance.needs_unloading)

    def test_sets_running_state_when_starting_run(self):
        # given
        self.appliance.update_power_consumption(2000)
        # when
        self.appliance.start_run()
        # then
        self.assertEqual(RunningState.RUNNING, self.appliance.running_state)

    def test_sets_start_and_finish_at_when_finishing_run(self):
        # given
        self.appliance.is_loaded = True
        self.appliance.power_state = PowerState.RUNNING
        # when
        self.appliance.finish_run()
        # then
        self.assertAlmostEqual(self.appliance.finished_last_run_at, datetime.now(), delta=timedelta(milliseconds=100))
        self.assertIsNone(self.appliance.started_run_at)

    def test_running_state_idle_when_finishing_run(self):
        # given
        self.appliance.is_loaded = True
        self.appliance.power_state = PowerState.RUNNING
        # when
        self.appliance.finish_run()
        # then
        self.assertEqual(RunningState.IDLE, self.appliance.running_state)

    def test_sets_needing_unload_when_finishing_run_loaded(self):
        # given
        self.appliance.is_loaded = True
        self.appliance.power_state = PowerState.RUNNING
        # when
        self.appliance.finish_run()
        # then
        self.assertTrue(self.appliance.is_loaded)
        self.assertTrue(self.appliance.needs_unloading)

    def test_no_need_to_unload_when_finishing_run_unloaded(self):
        # given
        self.appliance.is_loaded = False
        self.appliance.power_state = PowerState.RUNNING
        # when
        self.appliance.finish_run()
        # then
        self.assertFalse(self.appliance.is_loaded)
        self.assertFalse(self.appliance.needs_unloading)

    def test_loading_appliance(self):
        # given
        self.appliance.is_loaded = self.appliance.needs_unloading = False
        # when
        self.appliance.load()
        # then
        self.assertTrue(self.appliance.is_loaded)

    def test_loading_appliance_needing_unload(self):
        # given
        self.appliance.is_loaded = self.appliance.needs_unloading = False
        # when
        self.appliance.load(needs_unloading=True)
        # then
        self.assertTrue(self.appliance.is_loaded)
        self.assertTrue(self.appliance.needs_unloading)

    def test_no_need_to_unload_when_appliance_is_running(self):
        # given
        self.appliance.start_run()
        self.appliance.is_loaded = self.appliance.needs_unloading = False
        # when
        self.appliance.load(needs_unloading=True)
        # then
        self.assertFalse(self.appliance.needs_unloading)

    def test_unloading_appliance(self):
        # given
        self.appliance.is_loaded = self.appliance.needs_unloading = True
        # when
        self.appliance.unload()
        # then
        self.assertFalse(self.appliance.is_loaded)
        self.assertFalse(self.appliance.needs_unloading)

    def test_unloading_appliance_behaves_normal_when_running(self):
        # given
        self.appliance.start_run()
        # when
        self.appliance.unload()
        # then
        self.assertFalse(self.appliance.is_loaded)
        self.assertFalse(self.appliance.needs_unloading)

    def test_not_online_when_un_loading(self):
        # given
        self.appliance.last_seen_at = None
        # when
        self.appliance.load()
        self.appliance.unload()
        # then
        self.assertNotEqual(self.appliance.online_status(), OnlineStatus.ONLINE)

    def test_not_online_when_starting_or_finishing(self):
        # given
        self.appliance.last_seen_at = None
        # when
        self.appliance.start_run()
        self.appliance.finish_run()
        # then
        self.assertNotEqual(self.appliance.online_status(), OnlineStatus.ONLINE)

    def test_to_dict_has_mandatory_fields(self):
        last_updated_at = datetime.now()
        last_seen_at = datetime.now() - timedelta(seconds=5)
        power_state_appliance = ApplianceThatCanBeLoaded("test", "some appliance", 312.5,
                                                         last_updated_at=last_updated_at,
                                                         last_seen_at=last_seen_at)
        self.assertDictEqual(power_state_appliance.to_dict(),
                             {"name": "test", "type": "some appliance", "watt": 312.5,
                              "power_state": PowerState.RUNNING,
                              "needs_unloading": False, "is_loaded": False,
                              "started_run_at": None, "running_state": RunningState.UNKNOWN,
                              "finished_last_run_at": None, "online_status": OnlineStatus.ONLINE,
                              "last_updated_at": last_updated_at.isoformat(), "last_seen_at": last_seen_at.isoformat()})


if __name__ == '__main__':
    unittest.main()
