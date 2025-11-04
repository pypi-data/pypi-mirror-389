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

import importlib
import os
import sys
from typing import Union

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from tpds.helper import log
from tpds.usecase_collector.collector import Collector
from tpds.usecase_collector.usecase import Usecase, UsecaseEntrypoint


def load_app_root(api_inst: FastAPI) -> None:
    try:
        import tpds.app_root

        app_root_path = tpds.app_root.__path__[0]
        # Mount the base web app - Must be the last operation
        api_inst.mount("", StaticFiles(directory=app_root_path, html=True), name="approot")
    except ImportError:
        log(
            "Unable to find the application root resources - dependency tpds-application-root is missing"
        )


def _load_usecase(api_inst: FastAPI, usecase: Union[Usecase, UsecaseEntrypoint]) -> bool:
    backend = getattr(usecase, "backend", None)
    frontend = getattr(usecase, "frontend", None)

    if backend:
        if not all(item in sys.modules.keys() for item in backend.requires):
            return False

        bpath = backend.path
        if not os.path.isabs(bpath):
            bpath = os.path.join(usecase.source, bpath, "__init__.py")

        try:
            # Create a module import spec from the path to the __init__.py file that must be in the backend
            spec = importlib.util.spec_from_file_location(usecase.name, bpath)

            # Import the backend as module
            module_inst = importlib.util.module_from_spec(spec)

            # Add the module to our global namespace so it's available for use
            sys.modules[spec.name] = module_inst

            print(f"LOADING EXTENSION: {spec.name}")

            # Excute the module (i.e. load and bring in all the imports)
            spec.loader.exec_module(module_inst)

            if routers := getattr(backend, "routers", None):
                for router_name in routers:
                    router = getattr(module_inst, router_name, None)
                    if router is not None:
                        api_inst.include_router(router)
        except Exception as e:
            # Catch everything from the module to keep application stability
            log(
                f'Unable to load extension "{usecase.name}" from "{usecase.source}" with exception "{e}"'
            )
            # Skip frontend if backend can't be loaded
            frontend = None

    if frontend:
        if fpath := frontend.path:
            if not os.path.isabs(fpath):
                fpath = os.path.join(usecase.source, fpath)
        else:
            fpath = usecase.source

        if os.path.isdir(fpath) and os.path.exists(fpath):
            # The usecase should also have a frontend component - this will be attached as a static file
            api_inst.mount(
                f"/{usecase.name}", StaticFiles(directory=fpath, html=True), name=usecase.name
            )

    return True


def load_usecases(api_inst: FastAPI) -> None:
    remaining = list(Collector())

    while len(remaining):
        for usecase in remaining:
            if _load_usecase(api_inst, usecase):
                remaining.remove(usecase)
