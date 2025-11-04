from enum import Enum
from typing import Literal, Optional, Sequence, Union

from pydantic import BaseModel


class DeviceInterface(str, Enum):
    """
    The physical device interface - only applicable for secure elements
    """

    i2c = "i2c"
    spi = "spi"
    swi = "swi"


class DevicePartDetails(BaseModel):
    """
    Part Parametric Details
    """

    # Full Part Number
    partNumber: str
    # Device name (base part number)
    deviceName: str
    # Package Type
    packagePin: str
    # Interface Type
    partInterface: Optional[Sequence[DeviceInterface]]
    # Memory amount
    memory: Optional[str]
    # Shipping media - tray, bag, reel, etc
    media: Optional[str]
    # Minimum order quantity
    moq: Union[int, str, dict] = None
    # Production status information
    status: Optional[str]


class ProvisioningFlow(str, Enum):
    """
    Supported Provisioning Flows
    """

    tcsm = "TrustCUSTOM"
    tng = "Trust&Go"
    tflex = "TrustFLEX"
    tmng = "TrustMANAGER"


class ProvisioningFlowCategories(BaseModel):
    # Trust Custom Project Categories
    tcsm: Optional[Sequence[str]]
    # Trust&Go Project Categories
    tng: Optional[Sequence[str]]
    # Trust Flex Project Categories
    tflex: Optional[Sequence[str]]
    # TrustMANAGER Project Categories
    tmng: Optional[Sequence[str]]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "tcsm": "TrustCUSTOM",
            "tng": "Trust&Go",
            "tflex": "TrustFLEX",
            "tmng": "TrustMANAGER",
        }


class DeviceDetails(BaseModel):
    """
    TPDS Device Details
    """

    # Device Base Name
    basePart: str
    # Information Url
    partLink: Optional[str]
    # Default Tool Info
    toolLink: Optional[str]
    # Provisioning Flow Type
    provisioningFlow: Union[ProvisioningFlow, ProvisioningFlowCategories]
    # Product Category
    productCategory: Optional[str]
    # Part Type
    partType: Optional[str]
    # Interface Type
    partInterface: Optional[Sequence[DeviceInterface]]
    # TPDS Release Status
    tpdsRelease: Optional[bool] = False
    # NDA Status
    ndaRequired: Optional[bool] = True
    annualVolume: Union[int, None] = None
    certificates: Optional[list[str]] = []


class BoardInterface(str, Enum):
    """
    Board Communication Methods & Physical Layers
    """

    hid = "hid"
    uart = "uart"
    bridge = "bridge"


class BoardConnectionHid(BaseModel):
    """
    Ascii Kit Protocol Connection Details
    """

    interfaceType: Literal[BoardInterface.hid]
    vid: Optional[int] = 0x03EB
    pid: Optional[int] = 0x2312
    packetsize: Optional[int] = 64


class BoardConnectionUart(BaseModel):
    """
    UART/USART Ascii Kit Protocol Connection Details
    """

    interfaceType: Literal[BoardInterface.uart]
    port: Union[int, str] = 0
    baud: Optional[int] = 115200
    wordsize: Optional[int] = 8
    parity: Optional[int] = 0
    stopbits: Optional[int] = 1


class BoardConnectionBridge(BaseModel):
    """
    Bridge/Binary Kit Protocol Connection Details
    """

    interfaceType: Literal[BoardInterface.bridge]
    config: str


class PartInterfaceI2c(BaseModel):
    """
    I2C Interface details
    """

    interfaceType: Literal[DeviceInterface.i2c]
    address: Optional[int] = 0
    peripheralName: Optional[str]
    baud: Optional[int] = 100000


class PartInterfaceSpi(BaseModel):
    """
    SPI Interface Details
    """

    interfaceType: Literal[DeviceInterface.spi]
    address: Optional[int] = 0
    peripheralName: Optional[str]
    baud: Optional[int] = 1000000
    select: Union[str, int, None]


class PartInterfaceSwi(BaseModel):
    """
    Single Wire Interface Details
    """

    interfaceType: Literal[DeviceInterface.swi]
    address: Optional[int] = 0
    peripheralName: Optional[str]


class BoardDeviceDetails(BaseModel):
    """
    Device information and communication details for a board
    """

    # Connected Device Base Part
    deviceName: str
    # Interface Type
    # Should use a discriminator field here but
    # it won't get fixed until pydantic 1.9.1
    partInterface: Union[PartInterfaceI2c, PartInterfaceSpi, PartInterfaceSwi]


class BoardDetails(BaseModel):
    """
    Board/Kit Details
    """

    # Displayable description of the board
    description: str
    # Ordering Part number for the kit/board
    partNumber: Optional[str]
    # Online resources
    web_link: Optional[str]
    # Board image - url or local path
    img: Optional[str]
    # Metadata associated with the MCU
    serial_series: Optional[str]
    # Target MCU device
    mcu_part_number: Optional[str]
    # Name of the programming tool to use
    program_tool: Optional[str]
    # Kit Protocol parser application HID-USB PID
    kit_parser_pid: Optional[int] = 8978
    # Kit Protocol parser application version
    kit_parser_version: Optional[str] = "0.0.0"
    # kit_name
    kit_name: Optional[str] = ""
    # product string
    product_string: Optional[str] = ""
    # board path
    board_path: Union[str, None]
    # Connection Details
    # Should use a discriminator field here but
    # it won't get fixed until pydantic 1.9.1
    connection: Union[BoardConnectionHid, BoardConnectionUart, BoardConnectionBridge, None]
    # Connected Devices
    devices: Optional[Sequence[BoardDeviceDetails]]
