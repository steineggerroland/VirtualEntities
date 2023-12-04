import unittest
from random import randint

from iot.machine.PowerStateDecorator import PowerState
from iot.machine.WashingMachine import WashingMachine


class WashingMachineConstructionTest(unittest.TestCase):
    def test_name(self):
        washing_machine = WashingMachine('super_washing_machine')
        self.assertEqual(washing_machine.name, 'super_washing_machine')

    def test_unknown_watt(self):
        washing_machine = WashingMachine('washing_machine')
        self.assertEqual(washing_machine.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        washing_machine = WashingMachine('washing_machine', 0)
        self.assertEqual(washing_machine.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        washing_machine = WashingMachine('washing_machine', 4)
        self.assertEqual(washing_machine.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        washing_machine = WashingMachine('washing_machine', 400)
        self.assertEqual(washing_machine.power_state, PowerState.RUNNING)


class WashingMachineTest(unittest.TestCase):
    def setUp(self):
        self.washing_machine = WashingMachine('my-washing_machine', randint(0, 2300))

    def test_unknown_watt(self):
        self.washing_machine.update_power_consumption(None)
        self.assertEqual(self.washing_machine.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        self.washing_machine.update_power_consumption(0)
        self.assertEqual(self.washing_machine.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        self.washing_machine.update_power_consumption(5)
        self.assertEqual(self.washing_machine.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        self.washing_machine.update_power_consumption(450)
        self.assertEqual(self.washing_machine.power_state, PowerState.RUNNING)

    def test_to_dict_has_mandatory_fields(self):
        washing_machine = WashingMachine("test", 312.5)
        self.assertDictEqual(washing_machine.to_dict(),
                             {"name": "test", "watt": 312.5, "power_state": PowerState.RUNNING})


if __name__ == '__main__':
    unittest.main()
