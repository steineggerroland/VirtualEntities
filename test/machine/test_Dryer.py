import unittest
from random import randint

from iot.machine.Dryer import Dryer
from iot.machine.PowerStateDecorator import PowerState


class DryerConstructionTest(unittest.TestCase):
    def test_name(self):
        dryer = Dryer('super_dryer')
        self.assertEqual(dryer.name, 'super_dryer')

    def test_unknown_watt(self):
        dryer = Dryer('dryer')
        self.assertEqual(dryer.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        dryer = Dryer('dryer', 0)
        self.assertEqual(dryer.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        dryer = Dryer('dryer', 4)
        self.assertEqual(dryer.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        dryer = Dryer('dryer', 400)
        self.assertEqual(dryer.power_state, PowerState.RUNNING)


class DryerTest(unittest.TestCase):
    def setUp(self):
        self.dryer = Dryer('my-dryer', randint(0, 2300))

    def test_unknown_watt(self):
        self.dryer.update_power_consumption(None)
        self.assertEqual(self.dryer.power_state, PowerState.UNKNOWN)

    def test_zero_watt_is_off(self):
        self.dryer.update_power_consumption(0)
        self.assertEqual(self.dryer.power_state, PowerState.OFF)

    def test_low_watt_is_idle(self):
        self.dryer.update_power_consumption(5)
        self.assertEqual(self.dryer.power_state, PowerState.IDLE)

    def test_high_watt_is_running(self):
        self.dryer.update_power_consumption(450)
        self.assertEqual(self.dryer.power_state, PowerState.RUNNING)

    def test_to_dict_has_mandatory_fields(self):
        dryer = Dryer("test", 312.5)
        self.assertDictEqual(dryer.to_dict(), {"name": "test", "watt": 312.5, "power_state": PowerState.RUNNING})


if __name__ == '__main__':
    unittest.main()
