from models.responses.BaseResponse import BaseResponse
from typing import List, Optional
from models.Device import DeviceOut
import json

class DevicesListResponse(BaseResponse):
    data: Optional[List[DeviceOut]] = []