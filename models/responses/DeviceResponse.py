from models.responses.BaseResponse import BaseResponse
from typing import Optional
from models.Device import DeviceOut
import json

class DeviceResponse(BaseResponse):
    data: Optional[DeviceOut]
    def setDevice(self, device):
        self.data = DeviceOut(**device)