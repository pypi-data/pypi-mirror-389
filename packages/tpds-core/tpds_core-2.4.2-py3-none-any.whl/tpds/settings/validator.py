"""
Load and validate configurations
"""

from __future__ import annotations

import json
import os
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Any, Union

import jsonschema
import yaml

from tpds.helper import log


def _load_yaml_file(filename: Union[str, "os.PathLike[str]"]) -> dict[str, Any]:
    """
    Attempts to open a file and parse it as yaml
    """
    r_dict: dict[str, Any] = {}
    y_data = None
    with open(filename, "rb") as yamlfile:
        y_data = yaml.safe_load(yamlfile.read())
    if isinstance(y_data, dict):
        r_dict.update(y_data)
    else:
        r_dict[str(filename)] = y_data
    return r_dict


def _load_json_file(filename: Union[str, "os.PathLike[str]"]) -> dict[str, Any]:
    """
    Attempts to open a file and parse it as json
    """
    r_dict: dict[str, Any] = {}
    j_data = None
    with open(filename, "rb") as jsonfile:
        j_data = json.loads(jsonfile.read())
    if isinstance(j_data, dict):
        r_dict.update(j_data)
    else:
        r_dict[str(filename)] = j_data
    return r_dict


def _load_from_file(filename: Union[str, "os.PathLike[str]"]) -> dict[str, Any]:
    """
    Load configuration data from a file that could be either json or yaml
    """
    filename = Path(filename)
    if filename.suffix.lower() == "json":
        return _load_json_file(filename)
    return _load_yaml_file(filename)


def _load_data(data: Union[str, "os.PathLike[str]"]) -> dict[str, Any]:
    """
    Accept an arbitrary string and attempt to load it as json or yaml
    """
    if isinstance(data, os.PathLike) or os.path.exists(data):
        return _load_from_file(data)

    r_dict: dict[str, Any] = {}
    try:
        parsed_data = json.loads(data)
    except JSONDecodeError:
        parsed_data = yaml.safe_load(data)
    if isinstance(parsed_data, dict):
        r_dict.update(parsed_data)
    else:
        r_dict["data"] = parsed_data
    return r_dict


class SettingsValidator:
    """
    Class to validate usecase configuration
    """

    def __init__(self, schema: Union[str, dict[str, Any], "os.PathLike[str]"]) -> None:
        """
        Init for class variables
        """
        if isinstance(schema, dict):
            # Accept the provided dictionary as a valid schema
            self._usecase_schema = schema
        else:
            self._usecase_schema = _load_data(schema)

    def _validate(self, config: Union[str, dict[str, Any], "os.PathLike[str]"]) -> dict[str, Any]:
        if isinstance(config, dict):
            data = config
        else:
            data = _load_data(config)

        jsonschema.validate(instance=data, schema=self._usecase_schema)
        # Returns the validated instance if successful
        return data

    def validated(
        self, config: Union[str, dict[str, Any], "os.PathLike[str]"], debug: bool = False
    ) -> Union[dict[str, Any], None]:
        """
        Validate the provided configuration
        """
        try:
            return self._validate(config)
        except jsonschema.ValidationError as validation_exception:
            if debug:
                log(validation_exception)
            return None

    def validate(
        self, config: Union[str, dict[str, Any], "os.PathLike[str]"], debug: bool = False
    ) -> bool:
        """
        Validate the provided configuration
        """
        return self.validated(config, debug) is not None


def validator(config: os.PathLike[str], schema_file_name: str):
    schema = os.path.join(os.path.dirname(__file__), schema_file_name)
    validator = SettingsValidator(schema)
    return validator.validated(config, True)
