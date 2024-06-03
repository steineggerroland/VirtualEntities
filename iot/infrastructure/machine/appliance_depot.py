from typing import List

from iot.core.storage import Storage
from iot.infrastructure.machine.machine_that_can_be_loaded import MachineThatCanBeLoaded


class ApplianceDepot:
    def __init__(self, storage: Storage):
        self.storage = storage

    def stock(self, appliance: MachineThatCanBeLoaded) -> bool:
        """Stores a new appliance or updates an existing one."""
        return self.storage.update(appliance)

    def deplete(self, name: str) -> bool:
        """Removes an appliance from the depot."""
        return self.storage.remove(name)

    def retrieve(self, name: str) -> MachineThatCanBeLoaded | None:
        """Retrieves details of an appliance."""
        return self.storage.load_iot_machine(name)

    def inventory(self) -> List[MachineThatCanBeLoaded]:
        """Returns an inventory list of all appliances."""
        return self.storage.load_all_iot_machines()
