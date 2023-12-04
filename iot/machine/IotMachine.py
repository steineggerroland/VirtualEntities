class IotMachine:
    def __init__(self, name, watt):
        self.name = name
        self.watt = watt

    def update_power_consumption(self, watt):
        self.watt = watt

    def to_dict(self):
        return {"name": self.name, "watt": self.watt}
