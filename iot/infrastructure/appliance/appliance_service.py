import logging
import time
from threading import Thread
from typing import List

from python_event_bus import EventBus

from iot.core.configuration import VirtualEntityConfig
from iot.core.configuration_manager import ConfigurationManager
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.appliance.appliance_depot import ApplianceDepot
from iot.infrastructure.appliance.appliance_builder import ApplianceBuilder
from iot.infrastructure.appliance.appliance_that_can_be_loaded import ApplianceThatCanBeLoaded
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.appliance.run_complete_strategy import SimpleHistoryRunCompleteStrategy


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
        EventBus.subscribe("appliance/changed_config_name", self.change_name, priority=0)

    def add_appliance_by_config(self, entity_configs: List[VirtualEntityConfig]):
        for entity_config in entity_configs:
            appliance = self.appliance_depot.retrieve(entity_config.name)
            self.managed_appliances.add(
                ManagedAppliance(entity_config.name, SimpleHistoryRunCompleteStrategy(self.time_series_storage,
                                                                                      entity_config.run_complete_when.below_threshold_for,
                                                                                      entity_config.run_complete_when.threshold)))
            if appliance is None:
                appliance = ApplianceBuilder.from_dict(entity_config.__dict__)
                self.appliance_depot.stock(appliance)
            if appliance.started_run_at is not None:
                self.started_run(entity_config.name)
            EventBus.call("appliance/added", appliance)

    def update_power_consumption(self, appliance_name: str, new_power_consumption):
        try:
            appliance = self.appliance_depot.retrieve(appliance_name)
            appliance.update_power_consumption(new_power_consumption)
            self.appliance_depot.stock(appliance)
            self.time_series_storage.append_power_consumption(new_power_consumption, appliance_name)
            if appliance.started_run_at is None and appliance.power_state is PowerState.RUNNING:
                self.started_run(appliance_name)
            EventBus.call("appliance/updatedPowerConsumption", appliance)
        except ValueError as e:
            raise DatabaseException('Failed to save new power consumption because of database error.', e) from e

    def started_run(self, appliance_name: str):
        try:
            appliance = self.appliance_depot.retrieve(appliance_name)
            if not appliance.start_run:
                return
            appliance.start_run()
            self.appliance_depot.stock(appliance)
            managed_appliance = self.managed_appliances.find(appliance_name)
            managed_appliance.init_check_if_run_completed_thread(
                self._create_thread_for_is_running_check(managed_appliance))
            EventBus.call("appliance/startedRun", appliance)
        except ValueError as e:
            raise DatabaseException('Failed to save started run because of database error.', e) from e

    def _create_thread_for_is_running_check(self, managed_appliance):
        return Thread(target=self._scheduled_check, daemon=True,
                      args=[managed_appliance])

    def _scheduled_check(self, managed_appliance: ManagedAppliance):
        appliance = self.appliance_depot.retrieve(managed_appliance.name)
        while not managed_appliance.run_complete_strategy.is_run_completed(appliance):
            time.sleep(10)
            appliance = self.appliance_depot.retrieve(managed_appliance.name)
        self.finished_run(managed_appliance.name)

    def finished_run(self, name: str):
        try:
            appliance = self.appliance_depot.retrieve(name)
            appliance.finish_run()
            self.appliance_depot.stock(appliance)
            EventBus.call("appliance/finishedRun", appliance)
        except ValueError as e:
            raise DatabaseException("Failed to finish run of '%s' because of database error." % name, e) from e

    def unloaded(self, appliance_name: str):
        try:
            appliance = self.appliance_depot.retrieve(appliance_name)
            appliance.unload()
            self.appliance_depot.stock(appliance)
            EventBus.call("appliance/unloaded", appliance)
        except ValueError as e:
            raise DatabaseException('Failed to save unloading appliance because of database error.', e) from e

    def loaded(self, appliance_name: str, needs_unloading=False):
        try:
            appliance = self.appliance_depot.retrieve(appliance_name)
            appliance.load(needs_unloading)
            self.appliance_depot.stock(appliance)
            EventBus.call("appliance/loaded", appliance)
        except ValueError as e:
            raise DatabaseException('Failed to save setting appliance to loaded.', e) from e

    def change_name(self, name: str, old_name: str):
        managed_appliance = self.managed_appliances.find(old_name)
        if managed_appliance.has_running_check():
            managed_appliance.change_name(name, self._create_thread_for_is_running_check(managed_appliance))
        else:
            managed_appliance.change_name(name)
        appliance = self.appliance_depot.retrieve(old_name)
        appliance.rename(name)
        self.appliance_depot.deplete(old_name)
        self.appliance_depot.stock(appliance)
        self.time_series_storage.rename(name, old_name)

    def get_appliance(self, appliance_name: str) -> ApplianceThatCanBeLoaded:
        return self.appliance_depot.retrieve(appliance_name)


def supports_entity_type(entity_type) -> bool:
    return ApplianceBuilder.can_build(entity_type)
