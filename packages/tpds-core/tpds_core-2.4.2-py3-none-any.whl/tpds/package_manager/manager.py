"""
TPDS Package Management
"""
from __future__ import annotations

import argparse
import os
import re

try:
    from tabulate import tabulate
except ImportError:
    pass

from importlib.metadata import metadata
from typing import Any, Iterator, MutableMapping, Sequence, Union
from zipfile import ZipFile

from packaging.utils import parse_wheel_filename

# Trust Platform Modules
from tpds.helper import ProcessingUtils, TableIterator, check_internet_connection
from tpds.helper.logger import LogFacility
from tpds.settings.tpds_settings import TrustPlatformSettings
from tpds.settings.validator import SettingsValidator

# Package Manager Modules
from .data_models import PackageDetails
from .pip_client import PipPackageClient

# List of exposed objects
__all__ = ["PackageManager", "prettify_channel"]


class ManifestValidator(SettingsValidator):
    """
    Process and validate a manifest - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}

    def __new__(cls) -> Any:
        # Only ever allow one global instance of the validator so it stays consistant
        # during runtime
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, schema: Union[str, None] = None) -> None:
        if not self.__shared_state:
            if schema is None:
                schema = str(os.path.join(os.path.dirname(__file__), "packages_schema.yaml"))
            super(ManifestValidator, self).__init__(schema)


class Manifest:
    """
    Package Manifest
    """

    def __init__(self, validator: Union[SettingsValidator, None] = None) -> None:
        if validator is None:
            validator = ManifestValidator()

        self.packages = {}
        self.extensions = {}

        try:
            import tpds.packages

            manifest = tpds.packages.get_package_manifest()
        except ImportError:
            manifest = {"version": "1.0", "packages": {}, "extensions": {}}

        v_manifest = validator.validated(manifest, True)
        if v_manifest is not None:
            self.__dict__.update(v_manifest)

    def get_by_source(self, source):
        result = {}
        for k, v in self.packages.items():
            if source in v.get("source", {source: None}):
                result[k] = v
        for k, v in self.extensions.items():
            if source in v.get("source", {source: None}):
                result[k] = v
        return result


class PackageCache(MutableMapping[str, PackageDetails]):
    __shared_state: dict[str, Any] = {}

    def __new__(cls, *args, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        if "_data" not in self.__dict__:
            self._data = {}
        self._data.update(dict(*args, **kwargs))

    def __getitem__(self, __k: str) -> PackageDetails:
        return self._data[__k]

    def __delitem__(self, __k: str) -> None:
        self._data.__delitem__(__k)

    def __setitem__(self, __k: str, __v: PackageDetails) -> None:
        self._data[__k] = __v

    def __iter__(self) -> Iterator[PackageDetails]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return str(self._data)


def prettify_channel(channel: str) -> str:
    # Looks like the channel is already fine
    if len(channel) < 30:
        return channel

    # Just shorten it show it displays better
    return channel[:10] + "..." + channel[-10:]


class PackageManager:
    __headers = ["Package name", "Channel", "Installed version", "Latest version"]
    __extra_re = re.compile(r"^(?P<package>.+)\s+;.+\'(?P<extra>.+)\'$")
    __shared_state: dict[str, Any] = {}
    __licenses = {
        "Proprietary": open(
            os.path.join(os.path.dirname(__file__), "licenses", "mchp.txt"), "r"
        ).read()
    }

    def __new__(cls, **kwargs: Any) -> Any:
        # Only ever allow one global instance of the validator so it stays consistant
        # during runtime
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, processor: Any = None) -> None:
        if not self.__shared_state:
            self._logger = LogFacility()
            self._packages = PackageCache()
            self._proc = processor if processor else ProcessingUtils()
            self._clients = {}
            self._load_manifest()

            self._clients["pypi"] = PipPackageClient(
                self._manifest.get_by_source("pypi").keys(),
                index=TrustPlatformSettings().settings.pip_index,
                processor=self._proc,
            )

    def _load_manifest(self):
        self._manifest = Manifest()
        for pn, pd in self._manifest.packages.items():
            if pn in self._packages:
                if self._packages[pn].description is None:
                    self._packages[pn].description = pd["description"]
            else:
                if "conda" in pd["source"]:
                    chan = pd["source"]["conda"]["channel"]
                else:
                    chan = "pypi"
                self._packages[pn] = PackageDetails(
                    name=pn, description=pd["description"], channel=chan
                )

    def _refresh_package_list(
        self, _client, local: bool = True, remote: bool = True, **kwargs: Any
    ) -> None:
        if local:
            _client.update_local(**kwargs)
        if remote:
            _client.update_remote(**kwargs)

        for installed in _client.get_installed_packages():
            self._packages[installed.name] = installed
            data = metadata(installed.name)
            if not installed.description:
                installed.description = data.get("Summary")
            if not installed.extras:
                if extras := data.get_all("Requires-Dist"):
                    for extra in extras:
                        if m := self.__extra_re.match(extra):
                            md = m.groupdict()
                            if md["extra"] in installed.extras:
                                installed.extras[md["extra"]] += [md["package"]]
                            else:
                                installed.extras[md["extra"]] = [md["package"]]

        for avail in _client.get_available_packages():
            if avail.license_text is None:
                avail.license_text = self.__licenses.get(
                    avail.license if avail.license else "Proprietary", None
                )

            if installed := self._packages.get(avail.name, None):
                installed.latest = avail.latest
                if installed.license is None:
                    installed.license = avail.license
                if installed.license_text is None:
                    installed.license_text = avail.license_text
            else:
                self._packages[avail.name] = avail

    def get_proc(self):
        return self._proc

    def get_default_license(self):
        return self.__licenses.get("Proprietary")

    def refresh_package_list(self, local: bool = True, remote: bool = True, **kwargs: Any) -> None:
        self._logger.log(f"Refreshing package lists - local: {local}, remote: {remote}")
        for name, c in self._clients.items():
            self._logger.log(f"Refreshing {name} package lists - local: {local}, remote: {remote}")
            self._refresh_package_list(c, local, remote, **kwargs)

    def login(self, username: str, password: str, hostname: str, client: str = "pypi") -> None:
        """
        Provide the user credentials for logging into the system
        """
        if c := self._clients.get(client, None):
            c.login(username, password, hostname)
        else:
            raise ValueError(f"Unable to find a packaging client named {client}")

    def logout(self, client: str = None) -> None:
        """
        Log out of the system
        """
        if client is None:
            for c in self._clients.values():
                c.logout()
        else:
            if c := self._clients.get(client, None):
                c.logout()
            else:
                raise ValueError(f"Unable to find a packaging client named {client}")

    def is_logged_in(self, client: str = "pypi") -> Union[str, None]:
        if c := self._clients.get(client, None):
            return c.is_logged_in()
        else:
            raise ValueError(f"Unable to find a packaging client named {client}")

    def get_installed(self) -> Sequence[PackageDetails]:
        installed = []
        for c in self._clients.values():
            result = c.get_installed_packages()
            installed += result
        installed.sort(key=lambda x: x.name)
        return installed

    def get_packages(self, pattern: str = None) -> Sequence[PackageDetails]:
        if pattern:
            return list(filter(lambda x: pattern in x.name, self._packages.values()))
        else:
            return list(self._packages.values())

    def get_upgradable(self) -> Sequence[PackageDetails]:
        return list(
            filter(
                lambda p: p.installed and p.latest and p.installed < p.latest,
                self._packages.values(),
            )
        )

    def install(self, packages: Sequence[str], refresh: bool = True, **kwargs) -> int:
        """
        Install the selected packages if they are allowed to be installed/updated

        """
        if check_internet_connection():
            return self._clients["pypi"].install(packages, **kwargs)
        return -1

    def install_tpds_extn(self, zipPath: Union[str, os.PathLike]) -> int:
        """
        Install TPDS Extension From zip file
        """
        workingDir = os.path.join(TrustPlatformSettings().get_base_folder(), "tpds_extn_install")
        os.makedirs(workingDir, exist_ok=True)
        if not zipPath:
            return None
        returncode = 0
        with ZipFile(os.path.normpath(zipPath), "r") as zipObject:
            whlFiles = [
                zipObject.extract(fileName, workingDir)
                for fileName in zipObject.namelist()
                if fileName.endswith(".whl")
            ]
            if len(whlFiles):
                returncode += self.install(whlFiles, refresh=False, reinstall=False)
        return returncode

    def get_packages_formatted(self) -> str:
        return tabulate(
            TableIterator(
                self._packages.values(),
                ["name", ("channel", prettify_channel), "installed", "latest"],
            ),
            headers=self.__headers,
        )

    def getWheelDetails(self, zipPath: Union[str, os.PathLike]):
        packages_info = []
        workingDir = os.path.join(TrustPlatformSettings().get_base_folder(), "tpds_extn_install")
        os.makedirs(workingDir, exist_ok=True)
        with ZipFile(os.path.normpath(zipPath), "r") as zipObject:
            whlFiles = [
                zipObject.extract(fileName, workingDir)
                for fileName in zipObject.namelist()
                if fileName.endswith(".whl")
            ]
            if len(whlFiles):
                for whlFile in whlFiles:
                    name, version, _, _ = parse_wheel_filename(os.path.basename(whlFile))
                    packages_info.append({"name": name, "latest": str(version)})
        return packages_info


def package_manager_main():  # pragma: no cover
    def list(args):
        pacman = PackageManager()
        pacman.refresh_package_list()
        print(pacman.get_packages_formatted())

    parser = argparse.ArgumentParser(
        description="Package Manager for the Trust Platform Development Suite"
    )
    subparsers = parser.add_subparsers()

    parse_list = subparsers("list")
    parse_list.set_defaults(func=list)


if __name__ == "__main__":  # pragma: no cover
    package_manager_main()
