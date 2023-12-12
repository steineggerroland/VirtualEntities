import random
import unittest
from datetime import datetime, timedelta

from iot.infrastructure.machine.iot_machine import OnlineStatus, IotMachine
from iot.infrastructure.machine.power_state_decorator import PowerState


class ConstructionTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual(IotMachine('super machine').name, 'super machine')

    def test_watt_parameters(self):
        test_cases = [(None, PowerState.UNKNOWN), (0, PowerState.OFF), (1.3, PowerState.IDLE),
                      (1898, PowerState.RUNNING)]
        for parameters in test_cases:
            self._test_watt(parameters[0], parameters[1])

    def _test_watt(self, watt, state):
        machine = IotMachine('machine', watt)
        self.assertEqual(machine.watt, watt)
        self.assertEqual(machine.power_state, state)

    def test_online_status(self):
        self.assertEqual(IotMachine('machine').online_status(), OnlineStatus.UNKNOWN)
        machine_updated_now_and_online_delta_ten_seconds = IotMachine('machine',
                                                                      last_seen_at=datetime.now())
        self.assertEqual(machine_updated_now_and_online_delta_ten_seconds.online_status(), OnlineStatus.ONLINE)
        machine_without_online_delta = IotMachine('machine', online_delta_in_seconds=20,
                                                  last_seen_at=datetime.now() - timedelta(seconds=20 + 1))
        self.assertEqual(machine_without_online_delta.online_status(), OnlineStatus.OFFLINE)

    def test_to_dict_has_mandatory_fields(self):
        last_updated_at = datetime.now()
        last_seen_at = datetime.now() - timedelta(minutes=2)
        dryer = IotMachine("test", 312.5, last_updated_at=last_updated_at, last_seen_at=last_seen_at)
        self.assertDictEqual(dryer.to_dict(),
                             {"name": "test", "watt": 312.5, "online_status": OnlineStatus.ONLINE,
                              "power_state": PowerState.RUNNING, "last_updated_at": last_updated_at.isoformat(),
                              "last_seen_at": last_seen_at.isoformat()})


class IotMachineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = IotMachine('machine')

    def test_unknown_watt(self):
        self.machine.update_power_consumption(None)
        self.assertEqual(self.machine.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        self.machine.update_power_consumption(0)
        self.assertEqual(self.machine.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        self.machine.update_power_consumption(5)
        self.assertEqual(self.machine.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        self.machine.update_power_consumption(450)
        self.assertEqual(self.machine.power_state, PowerState.RUNNING)

    def test_is_online_when_consumption_updates(self):
        self.assertNotEqual(self.machine.online_status(), OnlineStatus.ONLINE)
        # when
        self.machine.update_power_consumption(random.randrange(start=0, stop=2200))
        # then
        self.assertEqual(self.machine.online_status(), OnlineStatus.ONLINE)

    def test_is_not_online_when_starting_or_finishing(self):
        self.assertNotEqual(self.machine.online_status(), OnlineStatus.ONLINE)
        # when
        self.machine.start_run()
        self.machine.finish_run()
        # then
        self.assertNotEqual(self.machine.online_status(), OnlineStatus.ONLINE)


if __name__ == '__main__':
    unittest.main()
