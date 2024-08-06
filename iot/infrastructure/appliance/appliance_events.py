from enum import Enum

from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.appliance.appliance import Appliance


class ApplianceEvents(str, Enum):
    ADDED = "appliance/added"
    CHANGED_CONFIG_NAME = "appliance/changedConfigName"
    UPDATED_POWER_CONSUMPTION = "appliance/updatedPowerConsumption"
    STARTED_RUN = "appliance/startedRun"
    FINISHED_RUN = "appliance/finishedRun"
    LOADED = "appliance/loaded"
    UNLOADED = "appliance/unloaded"
    CLEAN = "appliance/clean"
    NOTICE_DIRT = "appliance/noticeDirt"


class ApplianceEvent:
    def __init__(self, appliance: Appliance):
        self.appliance = appliance


class ApplianceConsumptionEvent(ApplianceEvent):
    def __init__(self, appliance: Appliance, measurement: ConsumptionMeasurement):
        super().__init__(appliance)
        self.measurement = measurement
