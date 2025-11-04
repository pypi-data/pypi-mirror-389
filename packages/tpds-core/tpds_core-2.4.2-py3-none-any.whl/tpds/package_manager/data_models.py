from __future__ import annotations

from typing import Dict, Mapping, Optional, Sequence, Union

from packaging.version import VERSION_PATTERN, Version
from pydantic import BaseModel


class SemVer(Version):
    """
    Wrap python packaging version with a pydantic validator class
    """

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern=VERSION_PATTERN,
            # some example postcodes
            examples=["2.0.0", "2.0.0-rc.2", "2.0.0-rc.1", "1.0.0", "1.0.0-beta"],
        )

    @classmethod
    def validate(cls, v):
        return v if isinstance(v, Version) else cls(v)


class PackageDependencies(BaseModel):
    # Conda packages
    conda: Optional[Sequence[str]] = []
    # Pip packages
    pypi: Optional[Sequence[str]] = []


class PackageDetails(BaseModel):
    # Package Name
    name: str
    # Source Channel
    channel: str
    # Description of the package
    description: Optional[str]
    # Installed Version
    installed: Union[SemVer, str, None] = None
    # Latest Version
    latest: Union[SemVer, str, None]
    # status
    isUpdated: bool = False
    # License Description String
    license: Optional[str]
    # Full license text
    license_text: Optional[str]
    # Dependencies
    dependencies: Sequence[PackageDependencies] = []
    # Optional Dependencies
    extras: Union[Mapping[str, PackageDependencies], Dict] = {}


class TpdsPackagingModel(BaseModel):
    # Required Packages
    required: PackageDependencies = PackageDependencies()
    # Conditional Packages depending on the feature
    optional: Optional[Mapping[str, Sequence[str]]] = {}
