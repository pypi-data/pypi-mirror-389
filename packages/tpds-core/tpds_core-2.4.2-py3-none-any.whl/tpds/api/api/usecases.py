# This file is governed by the terms outlined in the LICENSE file located in the root directory of
# this repository. Please refer to the LICENSE file for comprehensive information.

import os
import platform
import shutil
import subprocess
from typing import List, Mapping, Optional, Sequence, Any
from urllib.parse import unquote as urlunquote

from tpds.settings import TrustPlatformSettings
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel
from pathlib import Path

from tpds.settings.validator import validator
from tpds.usecase_collector.collector import Collector
from tpds.usecase_collector.usecase import UsecaseEntrypoint
from tpds.helper import log, open_folder
from tpds.tp_utils.tp_settings import TPSettings
from tpds.devices import TpdsBoards, TpdsDevices

homePath = TrustPlatformSettings().get_base_folder()

usecase_router = APIRouter()

Collector().add_usecase(
    UsecaseEntrypoint(
        path=None,
        root=os.path.dirname(__file__),
        name="atecc608_tflx_config",
        title="ATECC608-TFLXTLS Configurator",
        entry="ECC608 TFLXTLS Configurator.html",
        applications=["configurator"],
        devices=["ATECC608-TFLXTLS"],
    )
)


class UsecaseDetails(BaseModel):
    # Usecase Name
    name: Optional[str]
    # Usecase Title
    title: Optional[str]
    # Usecase Comment
    description: Optional[str]
    # Application types that apply to the usecase
    applications: Optional[Sequence[str]]
    # Devices supported by the usecase
    devices: Optional[Sequence[str]]
    # Boards supported by the usecase
    boards: Optional[Sequence[str]]
    productCategory: Optional[str]
    provisioningFlow: Optional[str]


class ResponseModel(BaseModel):
    status: bool = False
    message: Any = ""


class checkBoardsResponse(BaseModel):
    status: bool = False
    message: str = ""
    log: str = ""


response = ResponseModel()

_usecase_icon_responses = {
    200: {
        "content": {
            "image/png": {},
            "image/jpeg": {},
            "image/vnd.microsoft.icon": {},
        }
    },
}


def _usecase_details(uc):
    return uc.__dict__


def _usecase_first_match(usecase_name):
    usecases = Collector()
    for uc in usecases:
        if uc.name == usecase_name:
            return _usecase_details(uc)


@usecase_router.get("/details/{usecase_name}", response_model=UsecaseDetails)
def get_usecase_details(usecase_name: str):
    """
    Fetches the usecase details

    Parameters
    ----------
        usecase_name (str):       Name of the usecase as string

    Returns
    -------
        Return the usecase details based on the name
    """
    return _usecase_first_match(usecase_name)


@usecase_router.get(
    "/icon/{usecase_name}", response_class=FileResponse, responses=_usecase_icon_responses
)
def get_usecase_icon(usecase_name: str):
    """
    Fetches the usecase icon/image

    Parameters
    ----------
        usecase_name (str):       Name of the usecase as string

    Returns
    -------
        Return the usecase icon/image based on the name
    """
    details = _usecase_first_match(usecase_name)
    image_path = None

    if details:
        if isinstance(ico := details.get("icon", None), Mapping):
            image_path = ico["path"]

    if image_path is None:
        image_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../assets/favicon.ico")
        )

    return FileResponse(image_path)


def filter_usecase(uc):
    if any(app in uc.applications for app in ("configurator", "demo")):
        return False
    elif isinstance(uc, UsecaseEntrypoint):
        return True
    elif fe := getattr(uc, "frontend", None):
        return fe.path and fe.entrypoints is None
    return False


@usecase_router.get("/list", response_model=List)
def get_usecases():
    """
    Return the installed usecases

    Parameters
    ----------
        None

    Returns
    -------
        Return the installed usecases
    """

    usecases = [uc.name for uc in filter(filter_usecase, Collector())]
    return usecases


@usecase_router.get("/devices_list")
def get_devices_list():
    devices = set()
    [devices.update(uc.get("devices")) for uc in get_usecases_details()]
    return sorted(devices)


@usecase_router.get("/list_details", response_model=Sequence[UsecaseDetails])
def get_usecases_details():
    """
    List the installed usecases with details

    Parameters
    ----------
        None

    Returns
    -------
        Return the installed usecases
    """
    devices = TpdsDevices().devices
    usecases = [_usecase_details(uc).copy() for uc in Collector() if filter_usecase(uc)]
    usecases_list = []
    for usecase in usecases:
        try:
            device = devices.get(usecase.get("devices")[0])
            usecase["provisioningFlow"] = device.provisioningFlow.value
            usecase["productCategory"] = device.productCategory
            usecases_list.append(usecase)
        except BaseException as e:
            log(f"Parsing {usecase.get('name')} Failed with : {e}")
    return usecases_list


@usecase_router.get("/openFirmware/{usecase_name}")
def open_mplab(usecase_name: str):
    response.status = False
    response.message = "Error"
    try:
        collector = Collector()
        yamlPath = collector._Collector__usecases.get(usecase_name)._source
        usecaseInfo = validator(yamlPath, "usecase_schema.yaml")

        mplab_project_paths = []
        if fw_projects := usecaseInfo.get("firmware", None):
            fw_base_path = os.path.join(homePath, usecase_name, "firmware")
            # Copy from extension directory to working dir if not available in usecase dir
            if not os.path.exists(fw_base_path):
                shutil.unpack_archive(
                    os.path.join(os.path.dirname(yamlPath), "firmware.zip"),
                    fw_base_path)
            mplab_project_paths = [os.path.join(fw_base_path, fw_project) for fw_project in fw_projects]
            if mplab_ide_path := TPSettings().get_mplab_paths().get("ide_path"):
                # if mplab path set, open the firmware project with mplab
                args = [mplab_ide_path, "--open"]
                # opening MPLABX in new console to solve MPLABX closing when TPDS closes for Windows
                if platform.system() == "Windows":
                    args[1:1] = ["--console", "new"]
                args.extend(mplab_project_paths)
                subprocess.Popen(args)
                response.status = True
                response.message = "Opening MPLAB X IDE........"
            else:
                # open source folder if mplab path not set
                open_folder(fw_base_path)
                response.status = True
                response.message = "MPLAB X path is not set, \
                    Please set it in File -> Preferences \
                        \nOpening firmware folder........."
        else:
            open_folder(os.path.join(homePath, usecase_name))
            response.status = True
            response.message = "Firmware project is not avialable \n Opening resources folder"
    except BaseException as e:
        response.status = False
        response.message = f"Opening firmware project has faild with {e}"
    return response


@usecase_router.get("/usecaseInfo/{usecase_name}")
def get_usecase_yaml_data(usecase_name):
    """
    Retrieve and process YAML data for a specified use case.

    This function takes a usecase name as input and retrieves the corresponding YAML data.
    It processes the YAML data to include additional information such as the content of the 'Info'
    file, the transaction diagram path, help content, and supported boards information.

    Args:
        usecase_name (str): A string containing the usecase name.

    Returns:
        response (object): An object containing the status and message.
                           If successful, the message contains the processed use case information.
                           If an error occurs, the message contains the error details.
    """
    response.status = False
    response.message = "Error"
    try:
        if not (usecase := Collector()._Collector__usecases.get(usecase_name)):
            response.message = f"Unable to resolve {usecase_name.replace('_', ' ')} usecase"
            return response
        path = usecase._source
        if ".ipynb" in path:
            path = getattr(usecase, "url", None)
            jupyter_port = TrustPlatformSettings()._settings.app_settings.jupyter_port
            response.message = f"http://localhost:{jupyter_port}/voila/render/{path}"
            response.status = True
        else:
            assert (usecaseInfo := validator(path, "usecase_schema.yaml")), "Invalid usecase config"
            resources_path = os.path.dirname(path)
            infoFile = os.path.join(resources_path, usecaseInfo.get("info"))
            usecaseInfo.update({"info": Path(infoFile).read_text()})
            usecaseInfo.update(
                {
                    "transactionDiagram": os.path.join(
                        os.path.dirname(usecase._url), usecaseInfo.get("transactionDiagram")
                    )
                }
            )
            help = os.path.join(resources_path, usecaseInfo.get("help", None))
            assert os.path.exists(help), "Help File does not exits"
            usecaseInfo.update(
                {"help": os.path.join(os.path.dirname(usecase._url), usecaseInfo.get("help"))}
            )
            if boards := usecaseInfo.get("supportedBoards"):
                supportedBoards = [
                    {"description": TpdsBoards().get_board_info(board).description, "board": board}
                    for board in boards
                ]
                usecaseInfo.update({"supportedBoards": supportedBoards})
            response.status = True
            response.message = usecaseInfo
    except Exception as e:
        response.status = False
        response.message = f"Usecase information yaml data loading has failed with {e}"
    return response


@usecase_router.get("/openlog/{usecase_name}")
def open_usecae_log(usecase_name: str):
    try:
        log_file = os.path.join(homePath, usecase_name, "provision.log")
        open_folder(log_file)
        response.status = True
        response.message = f"Opening log {log_file}"
    except FileNotFoundError:
        response.status = False
        response.message = "Log not found please execute\
              usecase atleast once for Log"
    except Exception as e:
        response.status = False
        response.message = f"Opening Log Faild with {e}"
    return response


def jupyter_path(path):
    jupyter_port = TrustPlatformSettings()._settings.app_settings.jupyter_port
    for search_paths in Collector().get_search_paths():
        if os.path.exists(os.path.join(search_paths.get("path"), path)):
            return f"http://localhost:{jupyter_port}/voila/render/{path}"
    return None


@usecase_router.get("/opennotebook/{usecase_name}", response_model=ResponseModel)
def openNoteBook(usecase_name: str):
    response.status = False
    response.message = f"Unable to resolve {usecase_name.replace('_', ' ')}"
    if path := getattr(Collector()._Collector__usecases.get(usecase_name, {}), "url", None):
        if ".ipynb" in path.lower():
            if path := jupyter_path(urlunquote(path)):
                response.status = True
                response.message = path
    return response


@usecase_router.post("/workingdir/{usecase_name}", response_model=ResponseModel)
def open_usecase_working_dir(usecase_name: str):
    response = ResponseModel()
    try:
        working_dir = os.path.join(homePath, usecase_name)
        if os.path.exists(working_dir):
            open_folder(working_dir)
            response.status = True
        else:
            response.message = f"Usecase Working Directory({working_dir}) Dosen't Exits"
    except Exception as e:
        response.message = f"Opening Usecase Folder Faild with: {e}"
    finally:
        return response
