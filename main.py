import json
import uuid
import threading
from servers.uvicorn import UvicornServerThreaded
from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery, APIKey
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import Response
from models.Device import Device, DeviceOut, DeviceState
from models.responses.DeviceResponse import DeviceResponse
from models.responses.DevicesListResponse  import DevicesListResponse
from models.responses.BaseResponse import BaseResponse, ResponceStatusCode
from database import Database
 
lock = threading.Lock()
db = Database()


API_KEY = "1234567asdfgh"
API_KEY_NAME = "TOKEN"
api_key_query = APIKeyQuery(name=str.lower(API_KEY_NAME), auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
            api_key_header: str = Security(api_key_header), 
            api_key_query: str = Security(api_key_query)
                                                        ):
    if api_key_query == API_KEY:
        return api_key_query
    elif api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials")

app = FastAPI(title="ARM devices control API")

@app.get("/device/list", response_model=DevicesListResponse, tags=["device"])
#async def devices_get_list(api_key: APIKey = Depends(get_api_key)):
async def devices_get_list():
    response = DevicesListResponse()
    devices = db.devices.getAllUsed()

    if devices:
        for device in devices:
            response.data.append(DeviceOut(**device));
    
    return response

#Get device by uuid
@app.get("/device/{uuid}", response_model=DeviceResponse, tags=["device"])
async def device_get(uuid: str):
    response = DeviceResponse()
    device = None
    if uuid:
        device = db.devices.get(uuid)

    if device:
        response.setDevice(device)
    else:
        response.status.code = 1
        response.status.message = "Device not found"
    
    return response

@app.put("/device", response_model=DeviceResponse, tags=["device"])
async def device_create(model: str, ipxe_url: str):
    response = DeviceResponse()
    device = None
    lock.acquire()

    try:
        device = db.devices.getOneUnused(model)
        if device:
            device['uuid'] = str(uuid.uuid4())
            device['ipxe_url'] = ipxe_url
            device['state'] = str.lower(DeviceState.PROVISIONING.name)
            switch = db.switches.get(device['connected_switch']['id'])
            switch.EnablePoe(device['connected_switch']['port'])
            db.saveChanges()
    finally:
        lock.release()

    if device:
        response.setDevice(device)
    else:
        response.status.code = 3
        response.status.message = "All devices in pool are used now, try later"

    return response

@app.delete("/device/{uuid}", response_model=DeviceResponse, tags=["device"])
async def device_delete(uuid: str):
    response = DeviceResponse()
    device = None
    lock.acquire()

    try:
        device = db.devices.get(uuid)
        if not device:
            response.status.code = ResponceStatusCode.NOTFOUND
            return response
        else:
            device['state'] = str.lower(DeviceState.EARASING.name)
            switch = db.switches.get(device['connected_switch']['id'])
            switch.DisablePoe(device['connected_switch']['port'])
            switch.EnablePoe(device['connected_switch']['port'])
            response.setDevice(device)
            db.saveChanges()
    except:
        response.status.code = ResponceStatusCode.ERROR
    finally:
        lock.release()

    return response

@app.post("/device/{uuid}/reboot", response_model=DeviceResponse, tags=["device"])
async def device_reboot(uuid: str):
    response = DeviceResponse()
    device = None
    lock.acquire()

    try:
        device = db.devices.get(uuid)
        if not device:
            response.status.code = ResponceStatusCode.NOTFOUND
            return response
        elif device['state'] == str.lower(DeviceState.EARASING.name):
            response.status.code = ResponceStatusCode.TRYLATER
        else:
            device['state'] = str.lower(DeviceState.REBOOTING.name)
            switch = db.switches.get(device['connected_switch']['id'])
            switch.DisablePoe(device['connected_switch']['port'])
            switch.EnablePoe(device['connected_switch']['port'])
            db.saveChanges()
        
        response.setDevice(device)
    except:
        response.status.code = ResponceStatusCode.ERROR
    finally:
        lock.release()

    return response

@app.post("/device/{uuid}/poweroff", response_model=DeviceResponse, tags=["device"])
async def device_poweroff(uuid: str):
    response = DeviceResponse()
    device = None
    lock.acquire()

    try:
        device = db.devices.get(uuid)
        if not device:
            response.status.code = ResponceStatusCode.NOTFOUND
            return response
        elif device['state'] == str.lower(DeviceState.EARASING.name):
            response.status.code = ResponceStatusCode.TRYLATER
        else:
            device['state'] = str.lower(DeviceState.POWEROFF.name)
            switch = db.switches.get(device['connected_switch']['id'])
            switch.DisablePoe(device['connected_switch']['port'])
            db.saveChanges()

        response.setDevice(device)
    except:
        response.status.code =  ResponceStatusCode.ERROR
    finally:
        lock.release()

    return response

@app.post("/device/{uuid}/poweron", response_model=DeviceResponse, tags=["device"])
async def device_poweron(uuid: str):
    response = DeviceResponse()
    device = None
    lock.acquire()

    try:
        device = db.devices.get(uuid)
        if not device:
            response.status.code = ResponceStatusCode.NOTFOUND
            return response
        elif device['state'] == str.lower(DeviceState.EARASING.name):
            response.status.code = ResponceStatusCode.TRYLATER
        else:
            device['state'] = str.lower(DeviceState.POWERON.name)
            switch = db.switches.get(device['connected_switch']['id'])
            switch.EnablePoe(device['connected_switch']['port'])
            db.saveChanges()
            
        response.setDevice(device)
    except:
        response.status.code = 2
        response.status.message = "Failed to power on device"
    finally:
        lock.release()

    return response

@app.get("/system/device/{uuid}/after-earase-poweroff", include_in_schema=True, tags=["system-hide"])
async def device_ipxe_poweroff(uuid: str):
    device = None
    lock.acquire()

    try:
        device = db.devices.get(uuid)
        if device:
            device['state'] = str.lower(DeviceState.POWEROFF.name)
            device['uuid'] = ""
            device['ipxe_url'] = ""
            switch = db.switches.get(device['connected_switch']['id'])
            switch.DisablePoe(device['connected_switch']['port'])
            db.saveChanges()
    finally:
        lock.release()

    return "OK"


import time
if __name__ == '__main__':
    uvicorn = UvicornServerThreaded(app=app)
    uvicorn.start()
    uvicorn.join()