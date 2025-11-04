# (c) 2021 Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS".  NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
# PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT, SPECIAL,
# PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY
# KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP
# HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO THE
# FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN
# ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
# THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.

from typing import Mapping, Sequence

import cryptoauthlib as cal
from fastapi import HTTPException
from fastapi.routing import APIRouter

from tpds.devices import BoardDetails, DeviceDetails, DevicePartDetails, TpdsDevices
from tpds.usecase_collector import Collector

from ..schemas.hw import DeviceToolDetails

router = APIRouter()


@router.post("/connect")
def device_connect(device_info: BoardDetails):
    """
    Initialize the device connection.

    Parameters
    ----------
        device_info (DeviceConnectDetails):       Pydantic DeviceConnectDetails instance

    Returns
    -------
        Status - Success or Failure
    """

    if cal.get_device_type_id(device_info.name) is not None:
        device_cfg = cal.cfg_ateccx08a_kithid_default()

        device_cfg.devtype = cal.get_device_type_id(device_info.name)
        device_cfg.cfg.atcahid.vid = device_info.application_vid
        device_cfg.cfg.atcahid.pid = device_info.application_pid

        if device_info.interface.lower() == "i2c":
            device_cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
        elif device_info.interface.lower() == "spi":
            device_cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SPI_IFACE)
        elif device_info.interface.lower() == "swi":
            device_cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SWI_IFACE)
        else:
            return {"status": cal.Status.ATCA_BAD_PARAM, "description": "Unknown device interface"}

        device_cfg.cfg.atcahid.dev_identity = device_info.address
        return {"status": cal.atcab_init(device_cfg), "description": "atcab_init return status"}

    else:
        return {"status": cal.Status.ATCA_BAD_PARAM, "description": "Unknown device name"}


@router.post("/disconnect")
def device_disconnect():
    """
    Disconnect from device.

    Parameters
    ----------
        None

    Returns
    -------
        Status of disconnect operation
    """
    return {"status": cal.atcab_release(), "description": "atcab_release return status"}


@router.get("/list", response_model=Sequence[str])
def device_list():
    """
    Get the list of supported devices

    Parameters
    ----------
        None

    Returns
    -------
        Supported devices
    """
    return list(TpdsDevices().devices.keys())


@router.get("/details/", response_model=Mapping[str, DeviceDetails])
def device_details(device_name: str = None):
    """
    Get device details

    Parameters
    ----------
        name - Device partnumber or fragment

    Returns
    -------
        Supported device information
    """
    if device_name:
        name = device_name.upper()
        result = {k: v for k, v in TpdsDevices().devices.items() if name in k}
        if len(result):
            return result
        else:
            raise HTTPException(status_code=404, detail=f"Device(s) not found for: {name}")
    else:
        return TpdsDevices().devices


def _get_tool_list():
    usecases = Collector()
    devices = {}
    tools = []
    for name, info in TpdsDevices().devices.items():
        if info.toolLink:
            _name = name.lower().replace("-", "_") + "_tool"
            _title = "{} {}".format(
                name, "Configurator" if "configurator" in info.toolLink.lower() else "Information"
            )
            devices[name] = {
                "name": _name,
                "title": _title,
                "devices": [name],
                "url": info.toolLink,
                "toolType": "info_nda" if info.ndaRequired else "info",
            }

    for uc in usecases:
        if "configurator" in uc.applications:
            tools += [
                {
                    "name": uc.name,
                    "title": uc.title,
                    "devices": uc.devices,
                    "url": uc.url,
                    "toolType": "configurator",
                    "groupTitle": uc.groupTitle
                }
            ]
            for dev in uc.devices:
                devices.pop(dev, None)

    return sorted(tools + list(devices.values()), key=lambda x: x["name"].lower())


def _check_dev_list(device, device_list) -> bool:
    for _device in device_list:
        if device.lower() in _device.lower():
            return True
    return False


@router.get("/tools/", response_model=Sequence[DeviceToolDetails], response_model_exclude_none=True)
def device_tools(device_name: str = None):
    """
    List all of the installed tools

    Parameters
    ----------
        name - Device partnumber or fragment

    Returns
    -------
        Config tool details
    """
    if device_name:
        tools = list(filter(lambda x: _check_dev_list(device_name, x["devices"]), _get_tool_list()))
    else:
        tools = _get_tool_list()

    if len(tools):
        return tools
    else:
        raise HTTPException(status_code=404, detail="No tools found")


@router.get("/parts/", response_model=Sequence[DevicePartDetails], response_model_exclude_none=True)
def device_parts(device_name: str = None):
    """
    List all of part numbers known to TPDS

    Parameters
    ----------
        name - Device partnumber or fragment

    Returns
    -------
        Part details
    """
    if device_name:
        name = device_name.upper()
        parts = []
        for info in TpdsDevices().parts:
            if name in info.partNumber:
                parts += [info]

        if len(parts):
            return parts
        else:
            raise HTTPException(status_code=404, detail="No part info found for: {name}")
    else:
        return TpdsDevices().parts
