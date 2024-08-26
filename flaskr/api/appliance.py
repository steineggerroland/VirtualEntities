from iot.infrastructure.appliance.appliance import Appliance


class ApplianceConverter:
    def __init__(self, app):
        self.app = app

    def convert_appliance_for_frontend(self, appliance: Appliance) -> dict:
        to_dict = appliance.to_dict()
        if appliance.entity_type == 'dishwasher':
            to_dict['icon_url'] = self.app.url_for('static', filename='img/flaticon/dishwasher.png')
        elif appliance.entity_type == 'dryer':
            to_dict['icon_url'] = self.app.url_for('static', filename='img/flaticon/dryer.png')
        elif appliance.entity_type == 'washing_machine':
            to_dict['icon_url'] = self.app.url_for('static', filename='img/flaticon/washing_machine.png')
        else:
            to_dict['icon_url'] = self.app.url_for('static', filename='img/flaticon/unknown_box.png')
        return to_dict | {'representation': 'full'}

    def convert_appliance_for_frontend_without_context(self, appliance: Appliance) -> dict:
        return appliance.to_dict() | {'representation': 'reduced/no-urls'}
