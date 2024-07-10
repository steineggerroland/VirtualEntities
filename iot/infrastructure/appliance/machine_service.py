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
from iot.infrastructure.appliance.machine_builder import MachineBuilder
from iot.infrastructure.appliance.machine_that_can_be_loaded import MachineThatCanBeLoaded
from iot.infrastructure.appliance.power_state_decorator import PowerState
from iot.infrastructure.appliance.run_complete_strategy import SimpleHistoryRunCompleteStrategy


class ManagedMachine:
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


class ManagedMachines:
    def __init__(self):
        self._managed_machines = []

    def add(self, machine: ManagedMachine):
        self._managed_machines.append(machine)

    def find(self, name: str) -> ManagedMachine | None:
        matches = list(filter(lambda m: m.name == name, self._managed_machines))
        return matches[0] if matches else None


class MachineService:
    def __init__(self, appliance_depot: ApplianceDepot, time_series_storage: TimeSeriesStorage,
                 config_manager: ConfigurationManager):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.appliance_depot = appliance_depot
        self.time_series_storage = time_series_storage
        self.config_manager = config_manager
        self.managed_machines = ManagedMachines()
        EventBus.subscribe("appliance/changed_config_name", self.change_name, priority=0)

    def add_machines_by_config(self, entity_configs: List[VirtualEntityConfig]):
        for entity_config in entity_configs:
            machine = self.appliance_depot.retrieve(entity_config.name)
            self.managed_machines.add(
                ManagedMachine(entity_config.name, SimpleHistoryRunCompleteStrategy(self.time_series_storage,
                                                                                   entity_config.run_complete_when.below_threshold_for,
                                                                                   entity_config.run_complete_when.threshold)))
            if machine is None:
                machine = MachineBuilder.from_dict(entity_config.__dict__)
                self.appliance_depot.stock(machine)
            if machine.started_run_at is not None:
                self.started_run(entity_config.name)
            EventBus.call("appliance/added", machine)

    def update_power_consumption(self, machine_name: str, new_power_consumption):
        try:
            machine = self.appliance_depot.retrieve(machine_name)
            machine.update_power_consumption(new_power_consumption)
            self.appliance_depot.stock(machine)
            self.time_series_storage.append_power_consumption(new_power_consumption, machine_name)
            if machine.started_run_at is None and machine.power_state is PowerState.RUNNING:
                self.started_run(machine_name)
            EventBus.call("appliance/updatedPowerConsumption", machine)
        except ValueError as e:
            raise DatabaseException('Failed to save new power consumption because of database error.', e) from e

    def started_run(self, machine_name: str):
        try:
            machine = self.appliance_depot.retrieve(machine_name)
            if not machine.start_run:
                return
            machine.start_run()
            self.appliance_depot.stock(machine)
            managed_machine = self.managed_machines.find(machine_name)
            managed_machine.init_check_if_run_completed_thread(
                self._create_thread_for_is_running_check(managed_machine))
            EventBus.call("appliance/startedRun", machine)
        except ValueError as e:
            raise DatabaseException('Failed to save started run because of database error.', e) from e

    def _create_thread_for_is_running_check(self, managed_machine):
        return Thread(target=self._scheduled_check, daemon=True,
                      args=[managed_machine])

    def _scheduled_check(self, managed_machine: ManagedMachine):
        machine = self.appliance_depot.retrieve(managed_machine.name)
        while not managed_machine.run_complete_strategy.is_run_completed(machine):
            time.sleep(10)
            machine = self.appliance_depot.retrieve(managed_machine.name)
        self.finished_run(managed_machine.name)

    def finished_run(self, name: str):
        try:
            machine = self.appliance_depot.retrieve(name)
            machine.finish_run()
            self.appliance_depot.stock(machine)
            EventBus.call("appliance/finishedRun", machine)
        except ValueError as e:
            raise DatabaseException("Failed to finish run of '%s' because of database error." % name, e) from e

    def unloaded(self, machine_name: str):
        try:
            machine = self.appliance_depot.retrieve(machine_name)
            machine.unload()
            self.appliance_depot.stock(machine)
            EventBus.call("appliance/unloaded", machine)
        except ValueError as e:
            raise DatabaseException('Failed to save unloading appliance because of database error.', e) from e

    def loaded(self, machine_name: str, needs_unloading=False):
        try:
            machine = self.appliance_depot.retrieve(machine_name)
            machine.load(needs_unloading)
            self.appliance_depot.stock(machine)
            EventBus.call("appliance/loaded", machine)
        except ValueError as e:
            raise DatabaseException('Failed to save setting appliance to loaded.', e) from e

    def change_name(self, name: str, old_name: str):
        managed_machine = self.managed_machines.find(old_name)
        if managed_machine.has_running_check():
            managed_machine.change_name(name, self._create_thread_for_is_running_check(managed_machine))
        else:
            managed_machine.change_name(name)
        appliance = self.appliance_depot.retrieve(old_name)
        appliance.rename(name)
        self.appliance_depot.deplete(old_name)
        self.appliance_depot.stock(appliance)
        self.time_series_storage.rename(name, old_name)

    def get_machine(self, machine_name: str) -> MachineThatCanBeLoaded:
        return self.appliance_depot.retrieve(machine_name)


def supports_entity_type(entity_type) -> bool:
    return MachineBuilder.can_build(entity_type)
