# This file is governed by the terms outlined in the LICENSE file located in the root directory of
# this repository. Please refer to the LICENSE file for comprehensive information.

from tpds.usecase_collector.collector import Collector
from fastapi.routing import APIRouter
from .usecases import ResponseModel


demos_router = APIRouter()
response = ResponseModel()


def filter_demos(uc):
    if "demo" in uc.applications:
        return True
    return False


@demos_router.get("/demos_list", response_model=ResponseModel)
def get_demos_list():
    response.status = False
    response.message = "Failed to get Demos List"
    try:
        demos = [
            {
                "name": uc.name,
                "title": uc.title,
                "url": uc.url,
                "icon": uc.icon,
                "description": uc.description,
            }
            for uc in filter(filter_demos, Collector())
        ]
        response.status = True
        response.message = demos
    except Exception as e:
        response.message = f"Failed to get Demos List with Error: {e}"
    return response
