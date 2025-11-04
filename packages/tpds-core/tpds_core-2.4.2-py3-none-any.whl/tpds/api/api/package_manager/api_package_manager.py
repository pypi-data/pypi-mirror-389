# (c) Copyright (c) 2018-2023 Microchip Technology Inc. and its subsidiaries.
#
# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.
#
# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A
# PARTICULAR PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT,
# SPECIAL, PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE
# OF ANY KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF
# MICROCHIP HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE
# FORESEEABLE. TO THE FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL
# LIABILITY ON ALL CLAIMS IN ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED
# THE AMOUNT OF FEES, IF ANY, THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR
# THIS SOFTWARE.
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Union

from fastapi import UploadFile
from fastapi.routing import APIRouter
from tpds.app.vars import get_app_ref

from tpds.helper import log
from tpds.package_manager.manager import PackageManager
from tpds.settings.tpds_settings import reset_runtime_settings

router = APIRouter()


@router.get("/get_packages/{refresh}")
def get_packages(refresh: bool = False):
    manager = PackageManager()
    if refresh:
        manager.refresh_package_list(True, True)
    packages = manager.get_packages()
    for pack in packages:
        if pack.installed and pack.latest:
            pack.isUpdated = pack.installed >= pack.latest
        if pack.installed:
            pack.installed = str(pack.installed)
        if pack.latest:
            pack.latest = str(pack.latest)
    return packages


@router.post("/install/{packages}", response_model=int)
def install_packages(packages: str):
    packages = packages.split(",")
    return PackageManager().install(packages)


@router.post("/install_tpds_extn/", response_model=int)
async def install_tpds_extn(wheelZip: UploadFile):
    wheelPath = await getFilePath(wheelZip)
    return PackageManager().install_tpds_extn(wheelPath)


@router.post("/get_wheel_details/")
async def getWheelDetails(wheelZip: UploadFile):
    wheelPath = await getFilePath(wheelZip)
    return PackageManager().getWheelDetails(wheelPath)


@router.post("/shutdown/", response_model=bool)
def shutdown():
    app_ref = get_app_ref()
    if app_ref._view:
        log("shutdown")
        reset_runtime_settings()
        app_ref.stop_backend()
        log("quitting")
        app_ref.quit()
    else:
        return False


async def getFilePath(tempFile: UploadFile) -> Union[str, os.PathLike]:
    contents = await tempFile.read()
    op = NamedTemporaryFile("wb", delete=False)
    Path(op.name).write_bytes(contents)
    return op.name
