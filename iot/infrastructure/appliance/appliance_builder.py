from iot.infrastructure.appliance.appliance_that_can_be_loaded import ApplianceThatCanBeLoaded
from iot.infrastructure.exceptions import InvalidEntityType
from project import Project


class ApplianceBuilder:
    @staticmethod
    def from_dict(entry: dict) -> ApplianceThatCanBeLoaded:
        if 'type' not in entry or not ApplianceBuilder.can_build(entry['type']):
            raise InvalidEntityType()
        return ApplianceThatCanBeLoaded.from_dict(entry)

    @staticmethod
    def can_build(appliance_type: str) -> bool:
        return appliance_type in Project.appliance_types_that_can_be_loaded
