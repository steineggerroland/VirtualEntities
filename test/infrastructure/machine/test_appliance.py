import random
import unittest
from datetime import datetime, timedelta

from dateutil.tz import tzlocal

from iot.infrastructure.appliance.appliance import Appliance
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.virtual_entity import OnlineStatus


class ConstructionTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual(Appliance('super appliance', "some type").name, 'super appliance')

    def test_watt_parameters(self):
        test_cases = [(None, PowerState.UNKNOWN), (0, PowerState.OFF), (1.3, PowerState.IDLE),
                      (1898, PowerState.RUNNING)]
        for parameters in test_cases:
            self._test_watt(parameters[0], parameters[1])

    def _test_watt(self, watt, state):
        appliance = Appliance('appliance', "some type", watt)
        self.assertEqual(appliance.watt, watt)
        self.assertEqual(appliance.power_state, state)

    def test_online_status(self):
        self.assertEqual(Appliance('appliance', "some type").online_status(), OnlineStatus.UNKNOWN)
        appliance_updated_now_and_online_delta_ten_seconds = Appliance('appliance', "some type",
                                                                       last_seen_at=datetime.now(tzlocal()))
        self.assertEqual(appliance_updated_now_and_online_delta_ten_seconds.online_status(), OnlineStatus.ONLINE)
        appliance_without_online_delta = Appliance('appliance', "some type", online_delta_in_seconds=20,
                                                   last_seen_at=datetime.now(tzlocal()) - timedelta(seconds=20 + 1))
        self.assertEqual(appliance_without_online_delta.online_status(), OnlineStatus.OFFLINE)

    def test_to_dict_has_mandatory_fields(self):
        last_updated_at = datetime.now(tzlocal())
        last_seen_at = datetime.now(tzlocal()) - timedelta(minutes=2)
        dryer = Appliance("test", "some type", 312.5, last_updated_at=last_updated_at, last_seen_at=last_seen_at)
        self.assertDictEqual(dryer.to_dict(),
                             {"name": "test", "type": "some type", "watt": 312.5, "online_status": 'online',
                              "power_state": 'running', "last_updated_at": last_updated_at.isoformat(),
                              "last_seen_at": last_seen_at.isoformat()})


class ApplianceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.appliance = Appliance('appliance', "some type")

    def test_unknown_watt(self):
        self.appliance.update_power_consumption(None)
        self.assertEqual(self.appliance.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        self.appliance.update_power_consumption(0)
        self.assertEqual(self.appliance.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        self.appliance.update_power_consumption(5)
        self.assertEqual(self.appliance.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        self.appliance.update_power_consumption(450)
        self.assertEqual(self.appliance.power_state, PowerState.RUNNING)

    def test_is_online_when_consumption_updates(self):
        self.assertNotEqual(self.appliance.online_status(), OnlineStatus.ONLINE)
        # when
        self.appliance.update_power_consumption(random.randrange(start=0, stop=2200))
        # then
        self.assertEqual(self.appliance.online_status(), OnlineStatus.ONLINE)

    def test_is_not_online_when_starting_or_finishing(self):
        self.assertNotEqual(self.appliance.online_status(), OnlineStatus.ONLINE)
        # when
        self.appliance.start_run()
        self.appliance.finish_run()
        # then
        self.assertNotEqual(self.appliance.online_status(), OnlineStatus.ONLINE)


if __name__ == '__main__':
    unittest.main()
