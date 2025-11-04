from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence, Union

# Trust Platform Modules
from tpds.helper import LogFacility
from tpds.helper.processing import ProcessingUtils

from .data_models import PackageDependencies, PackageDetails


class PackageManagerClient(ABC):
    """
    Base class for package manager clients
    """

    def __init__(self, processor: Optional[Any] = None, **kwargs: Any) -> None:
        self._proc = processor if processor else ProcessingUtils()
        self._log = LogFacility()

    @abstractmethod
    def login(self, username: str, password: str, hostname: str, **kwargs: Any) -> None:
        """
        Provide the user credentials for logging into the system
        """

    @abstractmethod
    def logout(self, **kwargs: Any) -> None:
        """
        Log out of the system
        """

    @abstractmethod
    def is_logged_in(self, **kwargs: Any) -> Union[str, None]:
        """
        Check if the user is logged into the system
        """

    @abstractmethod
    def update_local(self, **kwargs: Any) -> None:
        """
        Update installed package information
        """

    @abstractmethod
    def update_remote(self, **kwargs: Any) -> None:
        """
        Retrieve the list of available packages and their versions
        """

    def update(self, **kwargs: Any) -> None:
        """
        Refresh all package information
        """
        self.update_local(**kwargs)
        self.update_remote(**kwargs)

    @abstractmethod
    def install(self, packages: Union[str, Sequence[str]], **kwargs) -> None:
        """
        Install the selected packages and their dependencies
        """

    @abstractmethod
    def update_dependency_list(
        self, packages: Union[str, Sequence[str]], **kwargs: Any
    ) -> PackageDependencies:
        """
        Dependencies are listed as part of additional metadata so we need to retrieve
        that information first before we execute additional steps
        """

    @abstractmethod
    def get_installed_packages(self, pattern: str) -> Sequence[PackageDetails]:
        """
        Get a list of installed tpds packages
        """

    @abstractmethod
    def get_available_packages(self, pattern: str) -> Sequence[PackageDetails]:
        """
        Get a list of all available packages that can be installed
        """

    @abstractmethod
    def get_dependencies(self, pattern: str) -> Sequence[PackageDetails]:
        """
        Get the list of dependencies
        """
