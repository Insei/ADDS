from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ConnectedSwitch(BaseModel):
    id: str
    port: str

class DeviceState(Enum):
    POWEROFF = 0
    POWERON = 1
    PROVISIONING = 2
    EARASING = 3
    REBOOTING = 4

class Device(BaseModel):
    id: int
    state: str
    serial: str
    mac: str
    vendor: str
    basemodel: str
    model: str
    power: str
    connected_switch: ConnectedSwitch
    ipxe_url: Optional[str]
    uuid: Optional[str]

class DeviceOut(BaseModel):
    uuid: str
    state: str
    serial: str
    mac: str
    model: str
    ipxe_url: str
    connected_switch: ConnectedSwitch