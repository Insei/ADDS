import json
import uuid
import threading
import os
from servers.uvicorn import UvicornServerThreaded
from servers.tftp import TftpServerThreaded
from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery, APIKey
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import Response
from models.Device import Device, DeviceOut, DeviceState
from models.responses.DeviceResponse import DeviceResponse
from models.responses.DevicesListResponse  import DevicesListResponse
from models.responses.BaseResponse import BaseResponse, ResponceStatusCode
from database import Database

main_dir = os.path.dirname(os.path.realpath(__file__))

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
tftp = TftpServerThreaded(os.path.join(main_dir, "tftp_root") + os.sep, os.path.join(main_dir, "images") + os.sep)

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
            device['state'] = str.lower(DeviceState.CREATING.name)
            # cp bootloader to tftp
            tftp.helper.make_bootloader(device['serial'], device['basemodel'], type="provisioning", ipxe_url_str=device['ipxe_url'])
            # power on by poe switch
            switch = db.switches.get(device['connected_switch']['id'])
            switch.EnablePoe(device['connected_switch']['port'])

            db.saveChanges()
    finally:
        lock.release()

    if device:
        response.setDevice(device)
    else:
        response.status.code = ResponceStatusCode.TRYLATER
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
            device['state'] = str.lower(DeviceState.ERASING.name)
            tftp.helper.make_bootloader(device['serial'], device['basemodel'], type="erase-sdcard")
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
        elif device['state'] == str.lower(DeviceState.ERASING.name) or device['state'] == str.lower(DeviceState.CREATING.name) or device['state'] == str.lower(DeviceState.PROVISIONING.name):
            response.status.code = ResponceStatusCode.TRYLATER
        else:
            device['state'] = str.lower(DeviceState.POWERON.name)
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
        elif device['state'] == str.lower(DeviceState.ERASING.name):
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
        elif device['state'] == str.lower(DeviceState.ERASING.name):
            response.status.code = ResponceStatusCode.TRYLATER
        else:
            device['state'] = str.lower(DeviceState.POWERON.name)
            switch = db.switches.get(device['connected_switch']['id'])
            switch.EnablePoe(device['connected_switch']['port'])
            db.saveChanges()
            
        response.setDevice(device)
    except:
        response.status.code  =  ResponceStatusCode.ERROR
        response.status.message = "Failed to power on device"
    finally:
        lock.release()

    return response

@app.get("/ipxe/{serial}/ipxe.efi.cfg", include_in_schema=True, tags=["ipxe-hide"])
async def ipxe_get_cfg(serial: str):
    ipxecfgfile = os.path.join(tftp.images_folder, "ipxe", "reboot-ipxe.efi.cfg")

    lock.acquire()
    try:
        device = db.devices.getBySerial(serial)
        if device:
            if device['state'] == str.lower(DeviceState.CREATING.name):
                ipxecfgfile = os.path.join(tftp.folder, device['serial'], "ipxe.efi.cfg")
                device['state'] = str.lower(DeviceState.PROVISIONING.name)
            elif device['state'] == str.lower(DeviceState.PROVISIONING.name):
                tftp.helper.make_bootloader(device['serial'], device['basemodel'], type="normal")
                ipxecfgfile = os.path.join(tftp.images_folder, "ipxe", "reboot-ipxe.efi.cfg")
                device['state'] = str.lower(DeviceState.POWERON.name)
            elif device['state'] == str.lower(DeviceState.ERASING.name):
                switch = db.switches.get(device['connected_switch']['id'])
                switch.DisablePoe(device['connected_switch']['port'])
                device['state'] = str.lower(DeviceState.POWEROFF.name)
                device['uuid'] = ""
                device['ipxe_url'] = ""
                tftp.helper.rmdir(device['serial'])
            db.saveChanges()
    except:
        print("ipxe_get_cfg: FAILED")
    finally:
        lock.release()

    return FileResponse(ipxecfgfile)


if __name__ == '__main__':
    uvicorn = UvicornServerThreaded(app=app)
    tftp.start()
    uvicorn.start()
    uvicorn.join()