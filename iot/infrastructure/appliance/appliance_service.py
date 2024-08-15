import logging
import time
from threading import Thread
from typing import List

from python_event_bus import EventBus

from iot.core.configuration import VirtualEntityConfig
from iot.core.configuration_manager import ConfigurationManager
from iot.core.time_series_storage import TimeSeriesStorage
from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.appliance.appliance import Appliance
from iot.infrastructure.appliance.appliance_builder import ApplianceBuilder
from iot.infrastructure.appliance.appliance_depot import ApplianceDepot
from iot.infrastructure.appliance.appliance_events import ApplianceEvents, ApplianceEvent, ApplianceConsumptionEvent
from iot.infrastructure.appliance.cleanable_appliance import CleanableAppliance
from iot.infrastructure.appliance.loadable_appliance import LoadableAppliance
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.appliance.run_complete_strategy import SimpleHistoryRunCompleteStrategy, \
    FinishedWhenChargingStrategy
from iot.infrastructure.exceptions import DatabaseException


class ManagedAppliance:
    def __init__(self, name, run_complete_strategy):
        self.name = name
        self.run_complete_strategy = run_complete_strategy
        self._check_if_run_completed_thread: Thread | None = None

    def init_check_if_run_completed_thread(self, thread):
        self._check_if_run_completed_thread = thread
        thread.start()

    def change_name(self, new_name: str, new_check_if_run_completed_thread: Thread | None = None):
        if self._check_if_run_completed_thread:
            self._check_if_run_completed_thread.join(0)
        self._check_if_run_completed_thread = new_check_if_run_completed_thread
        if self._check_if_run_completed_thread:
            self._check_if_run_completed_thread.start()
        self.name = new_name

    def has_running_check(self):
        return self._check_if_run_completed_thread is not None


class ManagedAppliances:
    def __init__(self):
        self._managed_appliances = []

    def add(self, appliance: ManagedAppliance):
        self._managed_appliances.append(appliance)

    def find(self, name: str) -> ManagedAppliance | None:
        matches = list(filter(lambda m: m.name == name, self._managed_appliances))
        return matches[0] if matches else None


class ApplianceService:
    def __init__(self, appliance_depot: ApplianceDepot, time_series_storage: TimeSeriesStorage,
                 config_manager: ConfigurationManager):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.appliance_depot = appliance_depot
        self.time_series_storage = time_series_storage
        self.config_manager = config_manager
        self.managed_appliances = ManagedAppliances()
        EventBus.subscribe(ApplianceEvents.CHANGED_CONFIG_NAME, self.change_name, priority=0)

    def add_appliance_by_config(self, entity_configs: List[VirtualEntityConfig]):
        for entity_config in entity_configs:
            self._setup_managed_appliance(entity_config)
            appliance = self._ensure_appliance_according_to_config_exists(entity_config)
            EventBus.call(ApplianceEvents.ADDED, ApplianceEvent(appliance))

            if appliance.started_run_at is not None:
                self.start_run(entity_config.name)

    def _setup_managed_appliance(self, entity_config):
        if entity_config.power_consumption_indicates_charging:
            run_complete_strategy = FinishedWhenChargingStrategy()
        else:
            run_complete_strategy = SimpleHistoryRunCompleteStrategy(self.time_series_storage,
                                                                     entity_config.run_complete_when.below_threshold_for_seconds,
                                                                     entity_config.run_complete_when.watt_threshold)
        self.managed_appliances.add(ManagedAppliance(entity_config.name, run_complete_strategy))

    def _ensure_appliance_according_to_config_exists(self, entity_config):
        appliance = self.appliance_depot.retrieve(entity_config.name)
        # apply config settings to appliance
        if appliance is None:
            appliance = ApplianceBuilder.from_dict(entity_config.__dict__)
        else:
            appliance = ApplianceBuilder.from_dict(appliance.to_dict() | entity_config.__dict__)
        self.appliance_depot.stock(appliance)
        return appliance

    def update_power_consumption(self, appliance_name: str, new_power_consumption):
        try:
            appliance = self.appliance_depot.retrieve(appliance_name)
            previous_run_finished_at = appliance.finished_last_run_at
            appliance = appliance.update_power_consumption(new_power_consumption)
            self.appliance_depot.stock(appliance)
            measurement = ConsumptionMeasurement(appliance.last_updated_at, new_power_consumption)
            self.time_series_storage.append_power_consumption(measurement, appliance_name)
            EventBus.call(ApplianceEvents.UPDATED_POWER_CONSUMPTION, ApplianceConsumptionEvent(appliance, measurement))
            # Verify if run started or finished
            if appliance.started_run_at is None and appliance.power_state is PowerState.RUNNING:
                self.start_run(appliance_name)
            elif previous_run_finished_at != appliance.finished_last_run_at:
                self.finish_run(appliance_name)
        except (ValueError, AttributeError) as e:
            raise DatabaseException(
                'Failed to save new power consumption for %s because of database error.' % appliance_name, e) from e

    def start_run(self, appliance_name: str):
        try:
            appliance = self.appliance_depot.retrieve(appliance_name).start_run()
            self.appliance_depot.stock(appliance)
            self.managed_appliances.find(appliance_name).init_check_if_run_completed_thread(
                self._create_thread_for_is_running_check(self.managed_appliances.find(appliance_name)))
            EventBus.call(ApplianceEvents.STARTED_RUN, ApplianceEvent(appliance))
        except ValueError as e:
            raise DatabaseException('Failed to save started run because of database error.', e) from e

    def _create_thread_for_is_running_check(self, managed_appliance):
        return Thread(target=self._scheduled_check, daemon=True, args=[managed_appliance])

    def _scheduled_check(self, managed_appliance: ManagedAppliance):
        appliance = self.appliance_depot.retrieve(managed_appliance.name)
        while not managed_appliance.run_complete_strategy.is_run_completed(appliance):
            time.sleep(10)
            appliance = self.appliance_depot.retrieve(managed_appliance.name)
        self.finish_run(managed_appliance.name)

    def finish_run(self, name: str):
        try:
            appliance = self.appliance_depot.retrieve(name).finish_run()
            self.appliance_depot.stock(appliance)
            EventBus.call(ApplianceEvents.FINISHED_RUN, ApplianceEvent(appliance))
        except ValueError as e:
            raise DatabaseException("Failed to finish run of '%s' because of database error." % name, e) from e

    def unloaded(self, appliance_name: str):
        try:
            appliance: LoadableAppliance = self.appliance_depot.retrieve(appliance_name).unload()
            self.appliance_depot.stock(appliance)
            EventBus.call(ApplianceEvents.UNLOADED, ApplianceEvent(appliance))
        except ValueError as e:
            raise DatabaseException(
                "Failed to save unloading appliance '%s' because of database error." % appliance_name, e) from e

    def loaded(self, appliance_name: str, needs_unloading=False):
        try:
            appliance: LoadableAppliance = self.appliance_depot.retrieve(appliance_name).load(needs_unloading)
            self.appliance_depot.stock(appliance)
            EventBus.call(ApplianceEvents.LOADED, ApplianceEvent(appliance))
        except ValueError as e:
            raise DatabaseException("Failed to save setting appliance '%s' to loaded." % appliance_name, e) from e

    def clean(self, name):
        try:
            appliance: CleanableAppliance = self.appliance_depot.retrieve(name).clean()
            self.appliance_depot.stock(appliance)
            EventBus.call(ApplianceEvents.CLEANED, ApplianceEvent(appliance))
        except ValueError as e:
            raise DatabaseException("Failed to save the cleaning of the appliance '%s'." % name, e) from e

    def notice_dirt(self, name, needs_cleaning=True):
        try:
            appliance: CleanableAppliance = self.appliance_depot.retrieve(name).notice_dirt(
                needs_cleaning=needs_cleaning)
            self.appliance_depot.stock(appliance)
            EventBus.call(ApplianceEvents.NOTICED_DIRT, ApplianceEvent(appliance))
        except ValueError as e:
            raise DatabaseException(
                "Failed to save noticing dirt of appliance '%s' with need to clean being %s." % (
                    name, needs_cleaning), e) from e

    def change_name(self, name: str, old_name: str):
        managed_appliance = self.managed_appliances.find(old_name)
        if managed_appliance.has_running_check():
            managed_appliance.change_name(name, self._create_thread_for_is_running_check(managed_appliance))
        else:
            managed_appliance.change_name(name)
        appliance = self.appliance_depot.retrieve(old_name).rename(name)
        self.appliance_depot.deplete(old_name)
        self.appliance_depot.stock(appliance)
        self.time_series_storage.rename(name, old_name)

    def get_appliance(self, appliance_name: str) -> Appliance:
        return self.appliance_depot.retrieve(appliance_name)


def supports_entity_type(entity_type) -> bool:
    return ApplianceBuilder.can_build(entity_type)
