import unittest
from unittest.mock import Mock

from iot.infrastructure.appliance.power_state_decorator import SimplePowerStateDecorator, PowerState


class PowerStateDecoratorInitTest(unittest.TestCase):
    def test_power_state_off_when_init_zero_watt(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = False
        appliance_mock.watt = 0
        watt_threshold = 10

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        self.assertEqual(appliance_mock.power_state, PowerState.OFF)

    def test_power_state_running_when_init_below_threshold(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = False
        watt_threshold = 10
        appliance_mock.watt = watt_threshold - 1

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        self.assertEqual(appliance_mock.power_state, PowerState.IDLE)

    def test_power_state_running_when_init_above_threshold(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = False
        watt_threshold = 10
        appliance_mock.watt = watt_threshold + 1

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        self.assertEqual(appliance_mock.power_state, PowerState.RUNNING)

    def test_power_state_charging_when_init_above_threshold_with_indicator(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = True
        watt_threshold = 10
        appliance_mock.watt = watt_threshold + 1

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        self.assertEqual(appliance_mock.power_state, PowerState.CHARGING)


class PowerStateDecoratorTest(unittest.TestCase):
    def test_power_state_off_when_zero_watt(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = False
        appliance_mock.watt = 0
        watt_threshold = 10

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        power_state.update_power_consumption(0)

        self.assertEqual(appliance_mock.power_state, PowerState.OFF)

    def test_power_state_idling_when_below_threshold(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = False
        appliance_mock.watt = 0
        watt_threshold = 10

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        power_state.update_power_consumption(watt_threshold - 1)

        self.assertEqual(appliance_mock.power_state, PowerState.IDLE)

    def test_power_state_running_when_above_threshold(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = False
        appliance_mock.watt = 0
        watt_threshold = 10

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        power_state.update_power_consumption(watt_threshold + 1)

        self.assertEqual(appliance_mock.power_state, PowerState.RUNNING)

    def test_power_state_charging_when_above_threshold_with_indicator(self):
        appliance_mock = Mock()
        appliance_mock.power_consumption_indicates_charging = True
        appliance_mock.watt = 0
        watt_threshold = 10

        power_state = SimplePowerStateDecorator(appliance_mock, watt_threshold=watt_threshold)
        power_state.update_power_consumption(watt_threshold + 1)

        self.assertEqual(appliance_mock.power_state, PowerState.CHARGING)


if __name__ == '__main__':
    unittest.main()
