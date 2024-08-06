import unittest
from datetime import datetime, timedelta

from dateutil.tz import tzlocal

from iot.infrastructure.appliance.appliance import RunningState
from iot.infrastructure.appliance.appliance_builder import ApplianceBuilder
from iot.infrastructure.appliance.cleanable_appliance import CleanableAppliance
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.virtual_entity import OnlineStatus


class CleanableApplianceInitTest(unittest.TestCase):
    def test_minimal_dict(self):
        name = "my super coffee machine"
        coffee_machine: CleanableAppliance = ApplianceBuilder.build_with(name=name, type="coffee_machine",
                                                                         is_cleanable=True)
        self.assertIsInstance(coffee_machine, CleanableAppliance)
        self.assertEqual(coffee_machine.name, name)
        self.assertEqual(coffee_machine.started_run_at, None)
        self.assertEqual(coffee_machine.finished_last_run_at, None)
        self.assertEqual(coffee_machine.needs_cleaning, False)
        self.assertEqual(coffee_machine.power_state, PowerState.UNKNOWN)
        self.assertEqual(coffee_machine.watt, None)
        self.assertEqual(coffee_machine.online_status(), OnlineStatus.UNKNOWN)
        self.assertEqual(coffee_machine.last_updated_at, None)

    def test_complete_dict(self):
        last_updated_at = datetime.now(tzlocal())
        started_run_at = datetime.now(tzlocal())
        running_state = RunningState.IDLE
        finished_last_run_at = datetime.now(tzlocal())
        last_seen_at = datetime.now(tzlocal()) - timedelta(seconds=5)
        name = 'super coffee maker 3k'
        watt = 255
        is_loaded = True
        needs_unloading = False
        coffee_machine: CleanableAppliance = ApplianceBuilder.build_with(name=name, type="coffee_machine",
                                                                        watt=watt,
                                                                        last_updated_at=last_updated_at,
                                                                        started_run_at=started_run_at,
                                                                        running_state=running_state,
                                                                        finished_last_run_at=finished_last_run_at,
                                                                        is_loaded=is_loaded,
                                                                        needs_unloading=needs_unloading,
                                                                        last_seen_at=last_seen_at,
                                                                        is_loadable=True)
        self.assertEqual(coffee_machine.name, name)
        self.assertEqual(coffee_machine.is_loaded, is_loaded)
        self.assertEqual(coffee_machine.needs_unloading, needs_unloading)
        self.assertEqual(coffee_machine.power_state, PowerState.RUNNING)
        self.assertEqual(coffee_machine.watt, watt)
        self.assertEqual(coffee_machine.online_status(), OnlineStatus.ONLINE)
        self.assertEqual(coffee_machine.last_updated_at, last_updated_at)
        self.assertEqual(coffee_machine.started_run_at, started_run_at)
        self.assertEqual(coffee_machine.running_state, running_state)
        self.assertEqual(coffee_machine.finished_last_run_at, finished_last_run_at)

    def test_to_dict_has_mandatory_fields(self):
        last_updated_at = datetime.now(tzlocal())
        last_seen_at = datetime.now(tzlocal()) - timedelta(seconds=5)
        appliance: CleanableAppliance = ApplianceBuilder.build_with(name="test", type="coffee_machine",
                                                                    watt=312.5,
                                                                    needs_cleaning=True,
                                                                    is_cleanable=True,
                                                                    last_updated_at=last_updated_at,
                                                                    last_seen_at=last_seen_at)
        self.assertDictEqual(appliance.to_dict(),
                             {"name": "test", "type": "coffee_machine", "watt": 312.5,
                              "power_state": PowerState.RUNNING,
                              "needs_cleaning": True,
                              "started_run_at": None, "running_state": RunningState.UNKNOWN,
                              "finished_last_run_at": None, "online_status": OnlineStatus.ONLINE,
                              "power_consumption_indicates_charging": False,
                              "last_updated_at": last_updated_at.isoformat(),
                              "last_seen_at": last_seen_at.isoformat(),
                              "is_cleanable": True})


class CleanableApplianceBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.appliance: CleanableAppliance = ApplianceBuilder.build_with(name='my-power_state_appliance',
                                                                         type="coffee_machine", watt=0,
                                                                         is_cleanable=True)

    def test_sets_no_need_for_cleaning_when_starting_run(self):
        # given
        self.appliance.needs_cleaning = True
        self.appliance.update_power_consumption(2000)
        # when
        self.appliance.start_run()
        # then
        self.assertFalse(self.appliance.needs_cleaning)

    def test_needs_cleaning_after_a_run(self):
        # given
        self.appliance.needs_cleaning = False
        self.appliance.power_state = PowerState.RUNNING
        # when
        self.appliance.finish_run()
        # then
        self.assertTrue(self.appliance.needs_cleaning)

    def test_needs_cleaning_when_noticing_dirt(self):
        # given
        self.appliance.needs_cleaning = False
        # when
        self.appliance.notice_dirt()
        # then
        self.assertTrue(self.appliance.needs_cleaning)

    def test_no_need_to_clean_when_appliance_is_running(self):
        # given
        self.appliance.needs_cleaning = True
        self.appliance.start_run()
        # when
        self.appliance.notice_dirt(needs_cleaning=True)
        # then
        self.assertFalse(self.appliance.needs_cleaning)

    def test_cleaning_appliance(self):
        # given
        self.appliance.needs_cleaning = True
        # when
        self.appliance.clean()
        # then
        self.assertFalse(self.appliance.needs_cleaning)

    def test_noticing_dirt_behaves_normal_when_running(self):
        # given
        self.appliance.start_run()
        # when
        self.appliance.notice_dirt(needs_cleaning=True)
        # then
        self.assertFalse(self.appliance.needs_cleaning)

    def test_not_online_when_un_loading(self):
        # given
        self.appliance.last_seen_at = None
        # when
        self.appliance.notice_dirt()
        self.appliance.clean()
        # then
        self.assertNotEqual(self.appliance.online_status(), OnlineStatus.ONLINE)


class CleanableApplianceKeepsBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.appliance: CleanableAppliance = ApplianceBuilder.build_with(name='my-power_state_appliance',
                                                                         type="coffee_machine", watt=0,
                                                                         is_cleanable=True)

    def test_sets_running_state_idle_when_off_after_updating_power_consumption(self):
        # given
        self.appliance.running_state = running_state = RunningState.UNKNOWN
        # when
        self.appliance.update_power_consumption(0)
        # then
        self.assertEqual(RunningState.IDLE, self.appliance.running_state)

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
        self.assertAlmostEqual(self.appliance.finished_last_run_at, datetime.now(tzlocal()),
                               delta=timedelta(milliseconds=100))
        self.assertIsNone(self.appliance.started_run_at)

    def test_running_state_idle_when_finishing_run(self):
        # given
        self.appliance.is_loaded = True
        self.appliance.power_state = PowerState.RUNNING
        # when
        self.appliance.finish_run()
        # then
        self.assertEqual(RunningState.IDLE, self.appliance.running_state)

    def test_sets_running_state_run_when_running_after_updating_power_consumption(self):
        # given
        self.appliance.running_state = RunningState.UNKNOWN
        # when
        self.appliance.update_power_consumption(2000)
        # then
        self.assertEqual(RunningState.RUNNING, self.appliance.running_state)

    def test_sets_start_at_when_starting_run(self):
        # given
        self.appliance.update_power_consumption(2000)
        # when
        self.appliance.start_run()
        # then
        self.assertAlmostEqual(self.appliance.started_run_at, datetime.now(tzlocal()),
                               delta=timedelta(milliseconds=100))


if __name__ == '__main__':
    unittest.main()
