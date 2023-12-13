from enum import Enum


class TemperatureUnit(str, Enum):
    DEGREE_CELSIUS = 'degree_celsius'


class Temperature:
    def __init__(self, value: float, unit=TemperatureUnit.DEGREE_CELSIUS):
        self.value: float = value
        self.unit: TemperatureUnit = unit

    def __eq__(self, other):
        if not isinstance(other, Temperature):
            return False
        return self.value == other.value and self.unit == other.unit
