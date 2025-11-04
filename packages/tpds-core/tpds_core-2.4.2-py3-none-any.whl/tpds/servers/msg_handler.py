from __future__ import annotations

import inspect
import os
import markdown
import subprocess
import sys
import typing
import webbrowser
from enum import Enum, IntEnum
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence, List, Union
from urllib.parse import unquote as urlunquote

from pydantic import BaseModel

from tpds.helper import log
from tpds.settings import TrustPlatformSettings
from tpds.usecase_collector import Collector

try:
    from types import GenericAlias
except ImportError:
    GenericAlias = type(List[int])

_GENERIC_ALIAS_FACTORIES = {
    typing.List: list,
    typing.Sequence: list,
    typing.MutableSequence: list,
    typing.Dict: dict,
    typing.Mapping: dict,
    typing.MutableMapping: dict
}


class ReservedMessageId(IntEnum):
    loopback = 0
    get_mplab_path = 1
    open_notebook = 2
    open_webview = 3
    tflex_provisioningXML = 4
    active_board = 5
    get_ta_appJSON = 6
    ta_open_app = 7
    ta_provisioningXML = 8
    tflx_proto_provisioning = 9
    ta_proto_provisioning = 10
    user_input_file_upload = 11
    user_input_text_box = 12
    user_input_dropdown = 13
    open_explorer_folder = 14
    open_configurator_page = 15
    tcustom_608_config_rw = 16
    open_default_browser = 17
    user_message_box = 18
    tflex_ecc204_json = 20
    tflex_ecc204_proto_prov = 21
    symm_auth_user_inputs = 40
    wpc_user_inputs = 41
    sha10x_symm_auth_user_inputs = 42
    provision_inputs = 50
    ta_appJSON = 80
    ta_uno_provisioningXML = 81
    ta_uno_get_config = 82
    reserved = 100


class ResponseCodes(str, Enum):
    OK = "OK"
    ERROR = "error"


class OperationMessage(BaseModel):
    # Requested Operation
    msg_id: Union[ReservedMessageId, int, str]
    # Parameters of the Operation
    parameters: Sequence[Any]
    # Optional field to identify the UI instance
    app_id: Optional[str] = ""


class ResponseMessage(BaseModel):
    # Requested Operation
    msg_id: Union[ReservedMessageId, int, str, None]
    # Response data
    response: Optional[str] = "unrecognized command"
    # Response error identifiers
    status: Union[ResponseCodes, str] = ResponseCodes.ERROR


@dataclass
class MessageContext:
    parent: Optional[Any]
    message: Optional[OperationMessage]
    client_id: Optional[str]


class Messages:
    __messages = {}

    def __init__(self, parent=None) -> None:
        self._parent = parent

    def decode(self, message, client_id: str = None):
        def default(*args):
            return ResponseMessage()

        msg = OperationMessage.parse_raw(message.encode("utf-8"))
        log(f"Processing Message: {msg}")
        ctx = MessageContext(self._parent, msg, client_id=client_id)
        return self.__messages.get(msg.msg_id, default)(ctx, *msg.parameters).json(
            exclude_none=True
        )

    @staticmethod
    def get_func_param_types(func):
        def _handle_annotation(a):
            if isinstance(a, str):
                a = eval(a.split("[")[0])

            if isinstance(a, GenericAlias):
                try:
                    return type(a())
                except TypeError:
                    return _GENERIC_ALIAS_FACTORIES[a]
            elif issubclass(a, inspect._empty):
                return object
            else:
                return a

        params = list(inspect.signature(func).parameters.values())
        is_class_member = params[0].name in ("self", "cls") if len(params) else False
        if is_class_member:
            params = params[1:]

        return [_handle_annotation(p.annotation) for p in params], is_class_member

    @classmethod
    def add(cls, id: Union[ReservedMessageId, int, str]) -> None:
        if isinstance(id, ReservedMessageId):
            id = int(id)
        elif isinstance(id, str):
            if id in ReservedMessageId.__members__.keys():
                raise ValueError(
                    f"{id} is a reserved value for {repr(getattr(ReservedMessageId,id))}. Provide a 'ReservedMessageId' enumeration instead"
                )
        elif isinstance(id, int):
            if id in ReservedMessageId.__members__.values():
                raise ValueError(
                    f"{id} is a reserved value for {repr(ReservedMessageId(id))}. Provide a 'ReservedMessageId' enumeration instead"
                )

        def decorator(func):
            arg_types, _ = cls.get_func_param_types(func)
            if not len(arg_types) or arg_types[0] != MessageContext:
                raise AttributeError(f"Invalid Signature for {func}")

            def wrapper(*args: str) -> ResponseMessage:
                log(f"{func.__name__}: " + " ".join([str(x) for x in args]))
                try:
                    response = func(*args)
                    if isinstance(response, tuple):
                        return ResponseMessage(response=response[1], status=response[0])
                    else:
                        return ResponseMessage(response=response, status="OK")
                except Exception as e:
                    return ResponseMessage(status=ResponseCodes.ERROR, response=str(e))

            cls.__messages[id] = wrapper
            return wrapper

        return decorator


@Messages.add(ReservedMessageId.open_notebook)
def open_notebook(ctx: MessageContext, usecase) -> str:
    if path := getattr(Collector().get(usecase, {}), "url", None):
        if ".ipynb" in path.lower():
            return (
                ctx.parent.get_jupyter_path(urlunquote(path)) + "?id=" + ctx.client_id
                if ctx.client_id
                else ""
            )
        else:
            return f"{path}"
    else:
        raise Exception(f"Unable to resolve {usecase}")


@Messages.add(ReservedMessageId.open_webview)
def open_webview(ctx: MessageContext, link_to_open: str):
    if "Documentation.html#" in link_to_open:
        render_path = f"http://localhost:{ctx.parent.backend._api_server.port}/{link_to_open}"
    elif os.path.exists(link_to_open):
        render_path = os.path.join(
            os.path.dirname(link_to_open),
            "Help-" + os.path.basename(link_to_open).split(".", 1)[0] + ".html",
        )
        Path(render_path).write_text(
            markdown.markdown(Path(link_to_open).read_text(), extensions=["toc"])
        )
        if "win" in sys.platform:
            render_path = "/" + render_path

        render_path = "file://" + render_path.replace("\\", "/")
    else:
        render_path = link_to_open

    ctx.parent.open_url(render_path)

    return render_path


@Messages.add(ReservedMessageId.loopback)
def loopback(ctx: MessageContext, *args) -> Optional[str]:
    return " ".join(args)


@Messages.add(ReservedMessageId.get_mplab_path)
def get_mplab_path(ctx: MessageContext) -> Optional[str]:
    conf = TrustPlatformSettings()
    return conf.settings.mplab_path


@Messages.add(ReservedMessageId.active_board)
def active_board(ctx: MessageContext, board_name) -> Optional[str]:
    config = TrustPlatformSettings()
    config.settings.runtime_settings.active_board = board_name
    config.save()
    return config.settings.runtime_settings.active_board


@Messages.add(ReservedMessageId.open_explorer_folder)
def open_explorer_folder(ctx: MessageContext, path) -> Optional[str]:  # pragma: no cover
    if sys.platform == "darwin":
        subprocess.check_call(["open", str(Path(path))])
    elif sys.platform == "linux":
        subprocess.check_call(["nautilus", str(Path(path))])
    elif sys.platform == "win32":
        subprocess.check_call(["explorer", str(Path(path))])
    return ""


@Messages.add(ReservedMessageId.open_default_browser)
def open_default_browser(ctx: MessageContext, page_str) -> Optional[str]:
    webbrowser.open(page_str)
    return page_str


__all__ = ["Messages", "ReservedMessageId", "ResponseCodes", "OperationMessage", "ResponseMessage"]
