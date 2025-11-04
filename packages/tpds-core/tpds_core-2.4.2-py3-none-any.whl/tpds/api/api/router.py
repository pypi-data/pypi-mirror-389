from fastapi import APIRouter

from .hw import api_board, api_device
from .manifest_file import api_manifest
from .package_manager import api_package_manager
from .demos import demos_router

api_router = APIRouter()
api_router.include_router(api_board.router, prefix="/boards", tags=["Boards"])
api_router.include_router(api_device.router, prefix="/device", tags=["Device"])
api_router.include_router(api_manifest.router, prefix="/manifest", tags=["Manifest"])
api_router.include_router(api_package_manager.router, prefix="/packman", tags=["Package Manager"])
api_router.include_router(demos_router, prefix="/demos", tags=["Demos"])
