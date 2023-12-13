import unittest

from iot.infrastructure.units import Temperature, TemperatureUnit


class TemperatureTest(unittest.TestCase):
    def test_value(self):
        value = 15.31
        self.assertEqual(Temperature(value=value).value, value)

    def test_equality(self):
        temperature = Temperature(value=15.31, unit=TemperatureUnit.DEGREE_CELSIUS)
        same_temperature = Temperature(value=15.31)
        self.assertEqual(temperature, same_temperature)

    def test_non_equality(self):
        temperature = Temperature(value=15.31, unit=TemperatureUnit.DEGREE_CELSIUS)
        different_temperature = Temperature(value=23, unit=TemperatureUnit.DEGREE_CELSIUS)
        self.assertNotEqual(temperature, different_temperature)


if __name__ == '__main__':
    unittest.main()
