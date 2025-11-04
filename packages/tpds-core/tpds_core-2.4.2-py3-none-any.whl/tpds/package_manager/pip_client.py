from __future__ import annotations

"""
Python Package Management (PIP) Client
"""

import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, Sequence, Union
from urllib.parse import ParseResult, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from packaging.utils import parse_wheel_filename

# Trust Platform Modules
from tpds.settings import TrustPlatformSettings

from .client_model import PackageManagerClient
from .data_models import PackageDependencies, PackageDetails


class PipPackageClient(PackageManagerClient):
    """
    Interact with the python packaging system
    """

    __rePipList = re.compile(
        r"^(?P<name>[\w\-]+)\s+(?P<installed>[\w\-\.]+)\s+((?P<loc>[\S]+)$|(?P<loc_tool>[\S]+)\s+(?P<tool>[\w]+)$)"
    )
    __rePipIndex = re.compile(r"^(?P<name>[\w\-]+)\s+\((?P<latest>[\w\-\.]+)\)")
    __cmdBase = [sys.executable, "-m", "pip"]

    def __init__(
        self,
        package_list: Sequence[str] = [],
        index: Optional[str] = None,
        preview: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._installed: dict[str, Any] = {}
        self._available: dict[str, Any] = {}
        self._search_list = package_list
        self._index: Optional[str] = index if index else "https://pypi.org/simple"
        self._preview_ok: bool = (
            preview if preview is not None else TrustPlatformSettings().settings.develop
        )

    def login(self, username: str, password: str, hostname: str) -> None:
        """
        Provide the user credentials for logging into the system
        """
        urlinfo = urlparse(hostname)._asdict()
        urlinfo["netloc"] = f"{username}:{password}@{urlinfo['netloc']}"
        self._index = urlunparse(ParseResult(**urlinfo))

    def logout(self) -> None:
        """
        Log out of the system
        """
        if self._index and "@" in self._index:
            urlinfo = urlparse(self._index)._asdict()
            urlinfo["netloc"] = urlinfo["netloc"].split("@")[1]
            self._index = urlunparse(ParseResult(**urlinfo))

    def is_logged_in(self) -> Union[str, None]:
        """
        Check if anyone is logged in
        """
        if self._index and "@" in self._index:
            urlinfo = urlparse(self._index)
            return urlinfo.username
        else:
            return None

    def update_local(self, **kwargs: Any) -> None:
        """
        Update the packaging information
        """
        cmd = self.__cmdBase + ["list", "-v"]
        outs, _ = self._proc.run_cmd(cmd, **kwargs)

        for line in outs.splitlines():
            if match := self.__rePipList.match(line):
                info = match.groupdict()
                if info["tool"] == "pip":
                    self._installed[info["name"]] = PackageDetails(**info, channel="pypi")

    @staticmethod
    def _pip_get_latest(packages: Sequence[PackageDetails], pre: bool = False) -> PackageDetails:
        # While it should likely be safe to grab the last entry in the list it appears that the list is
        # appended when a new package is uploaded which means that patch to a previous version would get
        # precedence over major/minor update that was published prior
        latest = None
        if packages:
            latest_ver = packages[0].latest
            for p in packages:
                if (p.latest > latest_ver and (pre or not p.latest.is_prerelease)) or (
                    p.latest == latest_ver
                ):
                    latest = p
                    latest_ver = p.latest
        return latest

    @staticmethod
    def _pip_parse_url(base, name, url):
        urldata = urlparse(url)

        if urldata.hostname is None:
            path = urljoin(f"{base}/{name}/", urldata.path)
        else:
            path = urldata.path
        name, version, _, _ = parse_wheel_filename(os.path.split(path)[-1])
        return PackageDetails(name=name, latest=version, url=path, channel="pypi")

    def _pip_get_package_data(self, package_name: str) -> Sequence[PackageDetails]:
        self._log.log(f"Retrieving versions: {self._index}/{package_name}")
        page = requests.get(f"{self._index}/{package_name}")
        soup = BeautifulSoup(page.text, "html.parser")
        links = soup.find_all("a", href=True)
        links = [
            self._pip_parse_url(self._index, package_name, a["href"])
            for a in filter(lambda x: x.text.lower().strip().endswith(".whl"), links)
        ]
        if details := self._pip_get_latest(links, self._preview_ok):
            self._log.log(f"{package_name}: {details.latest}")
        else:
            self._log.log(f"{package_name}: No info found")
        return details

    def update_remote(self, **kwargs: Any) -> None:
        """
        Retrieve the list of available packages and their versions
        """
        if "microchip.com" in self._index:
            search_list = list(filter(lambda x: x.startswith("tpds"), self._installed.keys()))
            search_list += list(self._search_list)
            search_list = list(set(search_list))
        else:
            search_list = list(self._search_list)

        try:
            with ThreadPoolExecutor() as exec:
                for p in exec.map(self._pip_get_package_data, search_list):
                    if p:
                        self._available[p.name] = p
        except BaseException as e:
            self._log.log(f"{e}")

    def _format_package_arg(self, package: str) -> str:
        if os.path.exists(package):
            return package
        if avail := self._available.get(package, None):
            return f"{package}=={avail.latest}"
        # This check makes sure we don't attempt to install a private package through this channel
        # unless it is a microchip hosted index
        if "microchip.com" in self._index or not any(
            n in package.lower() for n in ("tpds", "cryptoauth")
        ):
            return package

    def install(
        self, packages: Sequence[str], upgrade: bool = False, reinstall: bool = False, **kwargs: Any
    ) -> None:  # pragma: no cover
        """
        Install the selected packages and their dependencies
        """
        cmd = self.__cmdBase + ["install"]
        if self._index:
            cmd += ["-i", self._index]

        if reinstall:
            cmd += ["--force-reinstall"]

        if upgrade:
            cmd += ["--upgrade"]

        _packages = list(filter(lambda x: x, [self._format_package_arg(p) for p in packages]))
        _skipped = list(filter(lambda x: x not in _packages, packages))
        if _skipped:
            self._log.log(
                f"Unable to install or update the following packages: {', '.join(_skipped)}"
            )

        if _packages:
            cmd += _packages
            outs, returncode = self._proc.run_cmd(cmd, err_handling=self._proc.LOG, **kwargs)
            self._log.log(outs)
            self.update_local()
        else:
            returncode = 0

        return returncode

    def upgrade(self, packages: Sequence[str], **kwargs: Any) -> None:
        """
        Upgrade the selected packages to the latest versions
        """
        self.install(packages, upgrade=True, **kwargs)

    def update_dependency_list(
        self, packages: Union[str, Sequence[str]], channel: Optional[str] = None, **kwargs: Any
    ) -> PackageDependencies:
        """
        Dependencies are listed as part of additional metadata so we need to retrieve
        that information first before we execute additional steps
        """
        return PackageDependencies()

    def get_dependencies(self, pattern: str = "tpds") -> Sequence[PackageDetails]:
        """
        Get a list of dependencies we need to watch
        """
        return []

    def get_installed_packages(self, pattern: str = "tpds") -> Sequence[PackageDetails]:
        """
        Get a list of installed tpds packages
        """

        return list(filter(lambda x: pattern in x.name, self._installed.values()))

    def get_available_packages(self, pattern: str = "tpds") -> Sequence[PackageDetails]:
        """
        Get a list of all available packages that can be installed
        """
        return list(filter(lambda x: pattern in x.name, self._available.values()))


__all__ = ["PipPackageClient"]
