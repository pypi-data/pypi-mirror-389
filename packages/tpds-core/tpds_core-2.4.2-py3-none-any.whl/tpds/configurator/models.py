import datetime
import uuid
from enum import Enum
from typing import ForwardRef, Optional, Sequence, Union

from pydantic import BaseModel, SecretBytes

from .algorithms import KeyAlgorithms


class ConfigBaseModel(BaseModel):
    """
    Base model for configurator objects
    """

    # A unique identifier for the object
    id: uuid.UUID = uuid.uuid4()
    # User specified identifier that is often displayed
    name: Optional[str]
    # A helpful (displayable) description
    description: Optional[str]


class DataMapBase(BaseModel):
    """
    Base model for data mapping between an asset that will exist in a device and it's source
    """

    # A unique identifier for the object
    id: uuid.UUID = uuid.uuid4()
    # User specified identifier that is often displayed
    name: Optional[str]
    # A helpful (displayable) description
    description: Optional[str]


class DataMapStored(DataMapBase):
    """
    The source is stored somewhere in the device
    """

    # The source of the data
    source: ForwardRef("StoredDataBase")
    # Byte offset if the value is to be read
    offset: Optional[int]
    # Number of bytes to be read
    count: Optional[int]


class DataMapValue(DataMapBase):
    """
    The source is the provided value
    """

    # Value in bytes
    value: bytes


class DataMapSecretValue(DataMapBase):
    """
    The source is the provided value which is a secret value
    """

    # Value in bytes
    value: SecretBytes
    # Is the value secret
    secret: bool = True


class DataMapRandom(DataMapBase):
    """
    The source for the will be a random number from an approved RNG
    """

    from_hsm: bool = False


class DataMapGenerate(DataMapBase):
    """
    The source for the key will be a generation algorithm appropriate for the key type
    """

    from_hsm: bool = False
    # Only applicable when the key type is RSA
    exponent: Optional[bytes]


class DataMapGenerateSerialNumber(DataMapBase):
    """
    Generate Certificate Serial Numbers based on certificate data
    """

    # Final serial number size
    width: int


# Assets


class AssetBase(ConfigBaseModel):
    """
    Cryptographic assets that will generally be stored within the device
    """

    # Assets eventually need to get stored so they must have a handle
    handle: Optional[int]
    # If the asset won't be stored within the device then set stored to false
    stored: bool = True


# ******************************* Keys ***************************************


class KeyBase(AssetBase):
    # Cryptographic algorithm associated with the key
    algorithm: KeyAlgorithms


class PrivateKey(KeyBase):
    """
    Private keys that will be stored within the device
    """

    # Data for the key
    source: Union[DataMapValue, DataMapSecretValue, DataMapRandom, DataMapGenerate]


class PublicKey(KeyBase):
    """
    Asymmetric public keys which may be associated with stored private keys or PKIs
    """

    # Data for the key
    source: Union[DataMapValue, DataMapStored]
    # Is the public key a root public key
    root: bool = False
    # Occasionally public keys will be considered secret data
    secret: bool = False


class SymmetricKey(KeyBase):
    """
    Symmetric cryptographic keys used for things like HMAC & AES
    """

    # Data for the key
    source: Union[DataMapSecretValue, DataMapRandom]


# *************************** Certificates ***********************************


class CertificateBase(AssetBase):
    pass


class X509TimeFormat(str, Enum):
    Auto = "Auto"
    UTC_Time = "UTC_Time"
    Generalized_Time = "Generalized_Time"


class X509Time(BaseModel):
    format: X509TimeFormat
    value: datetime.datetime


class X509Name(BaseModel):
    common_name: Optional[str]
    surname: Optional[str]
    serial_number: Optional[str]
    country_name: Optional[str]
    locality_name: Optional[str]
    state_or_province_name: Optional[str]
    organization_name: Optional[str]
    organizational_unit_name: Optional[str]
    title: Optional[str]
    given_name: Optional[str]
    initials: Optional[str]
    generation_qualifier: Optional[str]
    dn_qualifier: Optional[str]
    pseudonym: Optional[str]
    domain_component: Optional[str]


class X509ExtensionBase(BaseModel):
    # Extension OID string
    oid: str
    # Must the extension be validated
    critical: Optional[bool] = False


class X509Certificate(CertificateBase):
    serial_number: Union[DataMapStored, DataMapGenerateSerialNumber]
    subject: X509Name
    subject_public_key_info: Union[PrivateKey, PublicKey]
    not_before: X509Time
    not_after: X509Time
    extensions: Sequence[X509ExtensionBase] = []
    issuer: ForwardRef("X509Certificate")


# ********************************* Data *************************************


class StoredDataBase(AssetBase):
    pass


class DigestTemplate(StoredDataBase):
    pass


# ******************************** Roles *************************************


class RoleBase(ConfigBaseModel):
    pass


# Device


class DeviceBase(ConfigBaseModel):
    pass


class CompleteConfiguration(ConfigBaseModel):
    assets: Sequence[Union[PrivateKey, PublicKey, SymmetricKey, X509Certificate]] = []
    device: Optional[DeviceBase]


# Update any forward refs that were used by the model definitions
DataMapStored.update_forward_refs()
X509Certificate.update_forward_refs()

# __all__ = []
