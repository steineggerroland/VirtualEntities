from datetime import datetime


class ConsumptionMeasurement:
    def __init__(self, time: datetime, consumption: float):
        self.time = time
        self.consumption = consumption

    def __repr__(self):
        return f"<ConsumptionMeasurement time={self.time}, consumption={self.consumption}>"


class TemperatureHumidityMeasurement:
    def __init__(self, time: datetime, temperature: float, humidity: float):
        self.time = time
        self.temperature = temperature
        self.humidity = humidity

    def __repr__(self):
        return f"<TemperatureHumidityMeasurement time={self.time}, temperature={self.temperature}, humidity={self.humidity}>"
