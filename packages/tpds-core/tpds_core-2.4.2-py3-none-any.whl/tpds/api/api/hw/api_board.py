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

import os
from typing import List, Optional

from fastapi import File, UploadFile
from fastapi.routing import APIRouter
from pykitinfo import pykitinfo
from tpds.flash_program import FlashProgram

from tpds.devices import TpdsBoards
from tpds.devices.tpds_models import BoardDetails
from tpds.helper import log

router = APIRouter()


@router.get("/get_details/{board_name}", response_model=Optional[BoardDetails])
def get_details(board_name: str):
    """
    Fetches the board details

    Parameters
    ----------
        board_name (str):       Name of the board as string

    Returns
    -------
        Return the board details based on the board name
    """
    return TpdsBoards().get_board_info(board_name)


@router.get("/get_supported", response_model=List)
def get_supported_boards():
    """
    Return the supported boards

    Parameters
    ----------
        None

    Returns
    -------
        Return the supported boards
    """
    supported_boards = []
    for board in TpdsBoards().boards.keys():
        supported_boards.append(board)

    return supported_boards


@router.get("/get_supported_details")
def get_supported_boards_details():
    """

    Retrieve a list of supported boards with their details.



    This function queries the available boards from the TpdsBoards and

    constructs a list of dictionaries, each containing the 'label' and 'value'

    of a supported board. The 'label' is derived from the board's description which is board's name,

    and the 'value' is the board's identifier.



    Parameters

    ----------

        None



    Returns

    -------

    list of dict

        A list of dictionaries, where each dictionary contains:

        - 'description': str, Name of the board.

        - 'board': str, the identifier of the board.

    """

    supported_boards = []

    for board, details in TpdsBoards().boards.items():

        supported_boards.append({"description": details.description, "board": board})

    return supported_boards


@router.get("/get_connected", response_model=List)
def get_connected_boards():
    """
    Function reads the .yaml file and check for the connected boards

    Parameters
    ----------
        None

    Returns
    -------
        Empty/board names based on what board are connected/recogonized
    """
    resp_boards = []
    all_kits = pykitinfo.detect_all_kits()
    for board, details in TpdsBoards().boards.items():
        if any(
            details.mcu_part_number == kit.get("debugger").get("device")
            or details.kit_name == kit.get("debugger", {}).get("kitname", "")
            for kit in all_kits
        ):
            resp_boards.append(board)

    return resp_boards


@router.post("/program/{board_name}")
async def program_hex_file(board_name: str, factory_hex_path: Optional[UploadFile] = File(None)):
    try:
        board_info = get_details(board_name)
        flash_program = FlashProgram(board_name, board_info)
        assert flash_program.is_board_connected(), "Check the Kit parser board connections"
        board_status = flash_program.check_board_status()
        log(f"Board Status: {board_status}")
        if board_status != "factory_programmed":
            factory_hex_path = os.path.join(board_info.board_path, board_name, f"{board_name}.hex")
            assert factory_hex_path, "Factory hex is unavailable to program"
            log(f"Factory hex path: {factory_hex_path}")
            status = flash_program.load_hex_image_with_ipe(factory_hex_path)
        else:
            status = "success"
    except BaseException as e:
        status = f"{e}"
    return status
