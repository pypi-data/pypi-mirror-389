from .tpds_boards import TpdsBoards
from .tpds_devices import TpdsDevices
from .tpds_models import BoardDetails, DeviceDetails, DeviceInterface, DevicePartDetails

__all__ = ["DeviceInterface", "DeviceDetails", "DevicePartDetails", "BoardDetails"]
__all__ += ["TpdsDevices", "TpdsBoards"]
