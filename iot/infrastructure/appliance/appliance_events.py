from enum import Enum

from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.appliance.appliance_that_can_be_loaded import ApplianceThatCanBeLoaded


class ApplianceEvents(str, Enum):
    ADDED = "appliance/added"
    CHANGED_CONFIG_NAME = "appliance/changed_config_name"
    UPDATED_POWER_CONSUMPTION = "appliance/updatedPowerConsumption"
    STARTED_RUN = "appliance/startedRun"
    FINISHED_RUN = "appliance/finishedRun"
    LOADED = "appliance/loaded"
    UNLOADED = "appliance/unloaded"


class ApplianceEvent:
    def __init__(self, appliance: ApplianceThatCanBeLoaded):
        self.appliance = appliance


class ApplianceConsumptionEvent(ApplianceEvent):
    def __init__(self, appliance: ApplianceThatCanBeLoaded, measurement: ConsumptionMeasurement):
        super().__init__(appliance)
        self.measurement = measurement
