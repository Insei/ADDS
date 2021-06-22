import json
import uuid
from models.Device import DeviceState
from models.Switch import Switch

class Switches:
    def __init__(self):
        self.pool = []

    def get(self, id: str):
         for switch in self.pool:
            if switch['id'] == id:
                return Switch(**switch)

class Devices:
    def __init__(self):
        self.pool = []

    def get(self, uuid: str):
        for device in self.pool:
            if device['uuid'] == uuid:
                return device

    def getOneUnused(self, model: str):
        for device in self.pool:
            if not device['uuid'] and device['model'] == model:
                return device

    def getAllUsed(self):
        devicesInUse = []
        for device in self.pool:
            if device['uuid']:
                devicesInUse.append(device)
        return devicesInUse

class Database:
    """
    **fake** database.
    """

    def __init__(self):
        self.devices_file = 'jsondb/devices.json'
        self.devices = Devices()
        with open(self.devices_file) as devices_json_file:
            self.devices.pool = json.load(devices_json_file)

        self.switches_file = 'jsondb/switches.json'
        self.switches = Switches()
        with open(self.switches_file) as switches_json_file:
            self.switches.pool = json.load(switches_json_file)

    def saveChanges(self):
        with open(self.devices_file, 'w') as devices_json_file:
            json.dump(self.devices.pool, devices_json_file, indent=4)


