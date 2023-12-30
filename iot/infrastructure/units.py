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

    def __str__(self):
        if self.unit == TemperatureUnit.DEGREE_CELSIUS:
            return f"{self.value}°C"
        else:
            return f"{self.value} {self.unit}"

    def to_dict(self):
        return {"value": self.value, "unit": self.unit}


def from_dict(dictionary: dict):
    return Temperature(value=dictionary['value'], unit=dictionary['unit'])


class Range:
    def __init__(self, lower_value: float, upper_value: float):
        self.lower_value = lower_value
        self.upper_value = upper_value

    def __eq__(self, other):
        if not isinstance(other, Range):
            return False
        return self.lower_value == other.lower_value and self.upper_value == other.upper_value

    def __str__(self):
        return f"({self.lower_value}:{self.upper_value})"


class TemperatureRating(str, Enum):
    UNKNOWN = "unknown"
    CRITICAL_COLD = "critical_cold"
    COLD = "cold"
    OPTIMAL = "optimal"
    HOT = "hot"
    CRITICAL_HOT = "critical_hot"


class TemperatureThresholds:
    def __init__(self, optimal: Range, frostiness_threshold: float, heat_threshold: float):
        self.optimal = optimal
        self.frostiness_threshold = frostiness_threshold
        self.heat_threshold = heat_threshold

    def __eq__(self, other):
        if not isinstance(other, TemperatureThresholds):
            return False
        return self.optimal == other.optimal and self.frostiness_threshold == other.frostiness_threshold and \
               self.heat_threshold == other.heat_threshold

    def __str__(self):
        return f"Temperature threshold with optimum at {self.optimal}, frostiness below {self.frostiness_threshold} " \
               f"and heat above {self.heat_threshold}"

    def to_dict(self) -> dict:
        return {"optimal_lower": self.optimal.lower_value, "optimal_upper": self.optimal.upper_value,
                "frostiness_threshold": self.frostiness_threshold, "heat_threshold": self.heat_threshold}


def temperature_thresholds_from_dict(dictionary: dict) -> TemperatureThresholds | None:
    if not dictionary:
        return None
    return TemperatureThresholds(optimal=Range(dictionary['optimal_lower'], dictionary['optimal_upper']),
                                 frostiness_threshold=dictionary['frostiness_threshold'],
                                 heat_threshold=dictionary['heat_threshold'])


class HumidityRating(str, Enum):
    UNKNOWN = "unknown"
    CRITICAL_DRY = "critical_dry"
    DRY = "dry"
    OPTIMAL = "optimal"
    WET = "wet"
    CRITICAL_WET = "critical_wet"


class HumidityThresholds:
    def __init__(self, optimal: Range, drought_threshold: float, wetness_threshold: float):
        self.optimal = optimal
        self.drought_threshold = drought_threshold
        self.wetness_threshold = wetness_threshold

    def __eq__(self, other):
        if not isinstance(other, HumidityThresholds):
            return False
        return self.optimal == other.optimal and self.drought_threshold == other.drought_threshold and self.wetness_threshold == other.wetness_threshold

    def __str__(self):
        return f"Humidity threshold with optimum at {self.optimal}, drought below {self.drought_threshold} " \
               f"and wetness above {self.wetness_threshold}"

    def to_dict(self) -> dict:
        return {"optimal_lower": self.optimal.lower_value, "optimal_upper": self.optimal.upper_value,
                "drought_threshold": self.drought_threshold, "wetness_threshold": self.wetness_threshold}


def humidity_thresholds_from_dict(dictionary: dict) -> HumidityThresholds | None:
    if not dictionary:
        return None
    return HumidityThresholds(optimal=Range(dictionary['optimal_lower'], dictionary['optimal_upper']),
                              drought_threshold=dictionary['drought_threshold'],
                              wetness_threshold=dictionary['wetness_threshold'])
