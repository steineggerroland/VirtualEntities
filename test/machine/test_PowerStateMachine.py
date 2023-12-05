import unittest
from datetime import datetime
from random import randint

from iot.machine.IotMachine import OnlineStatus
from iot.machine.PowerStateDecorator import PowerState
from iot.machine.PowerStateMachine import PowerStateMachine


class PowerStateMachineConstructionTest(unittest.TestCase):
    def test_name(self):
        power_state_machine = PowerStateMachine('super_power_state_machine')
        self.assertEqual(power_state_machine.name, 'super_power_state_machine')

    def test_unknown_watt(self):
        power_state_machine = PowerStateMachine('power_state_machine')
        self.assertEqual(power_state_machine.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        power_state_machine = PowerStateMachine('power_state_machine', 0)
        self.assertEqual(power_state_machine.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        power_state_machine = PowerStateMachine('power_state_machine', 4)
        self.assertEqual(power_state_machine.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        power_state_machine = PowerStateMachine('power_state_machine', 400)
        self.assertEqual(power_state_machine.power_state, PowerState.RUNNING)


class PowerStateMachineTest(unittest.TestCase):
    def setUp(self):
        self.power_state_machine = PowerStateMachine('my-power_state_machine', randint(0, 2300))

    def test_unknown_watt(self):
        self.power_state_machine.update_power_consumption(None)
        self.assertEqual(self.power_state_machine.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        self.power_state_machine.update_power_consumption(0)
        self.assertEqual(self.power_state_machine.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        self.power_state_machine.update_power_consumption(5)
        self.assertEqual(self.power_state_machine.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        self.power_state_machine.update_power_consumption(450)
        self.assertEqual(self.power_state_machine.power_state, PowerState.RUNNING)

    def test_to_dict_has_mandatory_fields(self):
        last_updated_at = datetime.now()
        power_state_machine = PowerStateMachine("test", 312.5, last_updated_at=last_updated_at)
        self.assertDictEqual(power_state_machine.to_dict(),
                             {"name": "test", "watt": 312.5, "power_state": PowerState.RUNNING,
                              "online_status": OnlineStatus.ONLINE, "last_updated_at": last_updated_at.isoformat()})


if __name__ == '__main__':
    unittest.main()
