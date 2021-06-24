# ASBDDS - is a simple ARM Single Board Devices Deployment System API.
This set of software and devices is used to automate the deployment of systems on arm single board devices.

#### The system includes: 
* HTTP server with API (running on 5000 port)
* TFTP server (running on 69 port)

#### The system needs:
* DHCP server in network
* Suported POE switch

#### Suported arm single board devices:
* Raspberry pi 4 (with POE power HAT)

#### Supported POE Swithes:
* TP-Link TL-SG2210MP

# We use:

## Fake database:
There is a preconfigured JSON pool of [devices](https://github.com/Insei/ASBDDS/blob/main/jsondb/devices.json) and JSON pool [poe switches](https://github.com/Insei/ASBDDS/blob/main/jsondb/devices.json). Devices and swithes in this pools adds manualy by redacting files, this is our fake db now.
Each device has a record to which switch and to which port it is [connected](https://github.com/Insei/ASBDDS/blob/main/jsondb/devices.json#L13).

## U-boot (as Bootloader and Storage cleaner)
We use 3 different build of u-boot for each device. Each build has a different boot command.
* [Storage cleaner](https://github.com/Insei/asbdds-u-boot/blob/asbds/configs/asbds_sdcard_erase_config#L5)
* [Default](https://github.com/Insei/asbdds-u-boot/blob/asbds/configs/asbds_config#L5)
* [IPXE booting](https://github.com/Insei/asbdds-u-boot/blob/asbds/configs/asbds_provisioning_config#L5)

## IPXE
We use ipxe in two variants:
* Default (For OS Installation)
* For API callbacks. (As example: u-boot after erasing storage boot wia ipxe, and get ipxe.cfg from the API at this moment we check the device state and if state is erasing - we switch device power to off on ethernet port switch and remove device uuid(makes device not in use))

## TFTP
We use TFTP server for provision bootloaders and ipxe to devices.
For each device in use we create folter in tftp root with device serial number and in this folder will be placed firmware, ipxe and bootloader files.
We switch bootloaders build's if this needed via api.

## DHCP
From DHCP devices get their IP address and get TFTP address. TFTP IP address is also IP address with our API.

## POE Switches
We use switches as power DC for single board arm devices. We manage POE power on ports via cli.

# Description of the processes of each API method.
## PUT /device/
Mark device from the pool of unused devices as used.
*parameters:* model and ipxe_url

1) Create device from the pool of devices, if unused device with this model exist in the pool.
2) Setup new uuid for this device for accessing to this device by uuid.
3) Copy firmware(if exist), bootloaders(u-boot ipxe build) and ipxe to folder with named as device serial in tftp root.
4) Setup ipxe url in the ipxe.efi.cfg in device root tftp folder.
5) Power on device via switch.
5) Setup state to "creating".
6) Return JSON response object with device data.
7) Device boot via PXE booting and load firmware(if exist) -> bootloader(u-boot).
8) Bootloader boot ipxe -> ipxe get serial number of device from SMBIOS and get TFTP address(via DHCP).
9) IPXE use serial and TFTP address to generate HTTP link to our API for getting IPXE cfg(TFTP server IP is also HTTP server IP).
10) After success installation OS from IPXE, device will be rebooted(This must be done by the operating system).

## GET /device/{UUID}/
Get device from the pool of used devices.
*parameters:* model and ipxe_url

1) Return JSON device data with specified uuid if exist.

## POST /device/{UUID}/reboot
Reboot device from the pool of used devices.

*parameters:* model and ipxe_url

1) Get device with specified uuid if exist.
2) Check that device state is allowing reboot, if not - return try later code.
3) Power OFF POE on port via cli on switch, then switch power to ON.
4) Setup device state to "poweron".
5) Return JSON response object with device data.

## POST /device/{UUID}/poweroff
Reboot device from the pool of used devices.
*parameters:* model and ipxe_url

1) Get device with specified uuid if exist.
2) Check that device state is allowing poweroff, if not - return try later code.
3) Power OFF POE on port via cli on switch.
4) Setup device state to "poweroff".
5) Return JSON response object with device data.

## POST /device/{UUID}/poweron
Reboot device from the pool of used devices.
*parameters:* model and ipxe_url

1) Get device with specified uuid if exist.
2) Check that device state is allowing power on, if not - return try later code.
3) Power ON POE on port via cli on switch.
4) Setup device state to "poweron".
5) Return JSON response object with device data.

## DELETE /device/{UUID}/
Remove device from the pool of used devices.
*parameters:* model and ipxe_url

1) Get device with specified uuid if exist.
2) Copy firmware(if exist), bootloaders(u-boot clean storage build) to folder with name as device serial in tftp root.
3) Reboot device via POE.
4) Device boot to u-boot and erasing storage -> u-boot boot ipxe.
5) IPXE get serial number of device from SMBIOS and get TFTP address(via DHCP).
9) IPXE use serial and TFTP address to generate HTTP link to our API for getting IPXE cfg(TFTP server IP is also HTTP server IP).
5) The device will shutdown when trying to get ipxe.cfg from our API.

## GET /ipxe/{serial}/ipxe.efi.cfg
Get ipxe.efi.cfg for device with specified serial.

1) Get device in use with specified serial if exist.
2) IF state of device "creating" > switch device state to "provisioning" and send ipxe.efi.cfg from tftp folder.
3) IF state of device "provisioning" > switch bootloader to normal mode and return reboot-ipxe.efi.cfg file from images/ipxe/ folder -> switch device state to "poweron" -> device will be rebooted by ipxe.
3) IF state of device "erasing" > remove device from device in use pool, clean uuid, clean ipxe url, and power off device by POE switch.
