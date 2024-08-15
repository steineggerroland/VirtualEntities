from enum import Enum

from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.appliance.appliance import Appliance


class ApplianceEvents(str, Enum):
    ADDED = "appliance/added"
    CHANGED_CONFIG_NAME = "appliance/changed-config-name"
    UPDATED_POWER_CONSUMPTION = "appliance/power-consumption/updated"
    STARTED_RUN = "appliance/run/started"
    FINISHED_RUN = "appliance/run/finished"
    LOADED = "appliance/loaded"
    UNLOADED = "appliance/unloaded"
    CLEANED = "appliance/cleaned"
    NOTICED_DIRT = "appliance/noticed-dirt"


class ApplianceEvent:
    def __init__(self, appliance: Appliance):
        self.appliance = appliance


class ApplianceConsumptionEvent(ApplianceEvent):
    def __init__(self, appliance: Appliance, measurement: ConsumptionMeasurement):
        super().__init__(appliance)
        self.measurement = measurement
