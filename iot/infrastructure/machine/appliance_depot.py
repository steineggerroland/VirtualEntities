from typing import List

from iot.core.storage import Storage
from iot.infrastructure.machine.iot_machine import IotMachine


class ApplianceDepot:
    def __init__(self, storage: Storage):
        self.storage = storage

    def stock(self, appliance: IotMachine) -> bool:
        """Stores a new appliance or updates an existing one."""
        return self.storage.update(appliance)

    def deplete(self, name: str) -> bool:
        """Removes an appliance from the depot."""
        return self.storage.remove(name)

    def retrieve(self, name: str) -> IotMachine:
        """Retrieves details of an appliance."""
        return self.storage.load_iot_machine(name)

    def inventory(self) -> List[IotMachine]:
        """Returns an inventory list of all appliances."""
        return self.storage.load_all_iot_machines()  # Assuming this method loads all appliances
