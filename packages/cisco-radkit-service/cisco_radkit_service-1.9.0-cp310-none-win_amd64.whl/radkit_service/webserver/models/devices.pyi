from .base import DontUpdate, RADKitBaseModel, RADKitRootModel, UpdateField, UpdateModel
from .labels import UpdateLabelSet
from _typeshed import Incomplete
from collections.abc import Sequence
from pydantic import ValidationInfo
from pydantic.types import UUID4
from radkit_common.terminal_interaction import ProvisioningVariant
from radkit_common.types import AnnotatedCustomSecretStr, ConnectionMethod, CustomSecretStr, DeviceType, HTTPProtocol, PortRanges, TerminalCapabilities
from typing import Annotated, Any, Literal
from typing_extensions import Self
from uuid import UUID

__all__ = ['StoredDevice', 'StoredDevices', 'StoredDeviceWithMetadata', 'StoredDevicesWithMetadata', 'DeviceSummary', 'NewDevice', 'NewDevices', 'BaseUpdateDevice', 'UpdateDevice', 'UpdateDevices', 'UpdateDevicesUniform', 'DeviceUUIDs', 'MetaDataEntry', 'JumphostName', 'StoredTerminal', 'NewTerminal', 'UpdateTerminal', 'StoredNetconf', 'NewNetconf', 'UpdateNetconf', 'StoredSNMP', 'NewSNMP', 'UpdateSNMP', 'StoredSwagger', 'NewSwagger', 'UpdateSwagger', 'StoredHTTP', 'NewHTTP', 'UpdateHTTP', 'StoredDeviceTemplateRef', 'NewDeviceTemplateRef', 'UpdateDeviceTemplateRef']

class StoredTerminal(RADKitBaseModel):
    connectionMethod: ConnectionMethod
    port: int
    username: str
    enableSet: bool
    useInsecureAlgorithms: bool
    jumphost: bool
    useTunnelingIfJumphost: bool
    provisioningVariant: ProvisioningVariant
    capabilities: frozenset[TerminalCapabilities]

class NewTerminal(RADKitBaseModel):
    connectionMethod: Literal[ConnectionMethod.SSH, ConnectionMethod.TELNET, ConnectionMethod.SSHPUBKEY, ConnectionMethod.TELNET_NO_AUTH]
    port: int
    username: str
    password: AnnotatedCustomSecretStr
    privateKeyPassword: AnnotatedCustomSecretStr
    privateKey: AnnotatedCustomSecretStr
    enableSet: bool
    enable: AnnotatedCustomSecretStr
    useInsecureAlgorithms: bool
    jumphost: bool
    useTunnelingIfJumphost: bool
    provisioningVariant: ProvisioningVariant
    capabilities: frozenset[TerminalCapabilities]
    @classmethod
    def validate_port_in_range(cls, port: int) -> int: ...
    def validate_private_key(cls, private_key: CustomSecretStr, info: ValidationInfo) -> CustomSecretStr: ...

class UpdateTerminal(UpdateModel):
    connectionMethod: UpdateField[Literal[ConnectionMethod.SSH, ConnectionMethod.TELNET, ConnectionMethod.SSHPUBKEY, ConnectionMethod.TELNET_NO_AUTH]]
    port: UpdateField[int]
    username: UpdateField[str]
    password: UpdateField[AnnotatedCustomSecretStr]
    privateKeyPassword: CustomSecretStr
    privateKey: UpdateField[AnnotatedCustomSecretStr]
    enableSet: UpdateField[bool]
    enable: UpdateField[AnnotatedCustomSecretStr]
    useInsecureAlgorithms: UpdateField[bool]
    jumphost: UpdateField[bool]
    useTunnelingIfJumphost: UpdateField[bool]
    provisioningVariant: UpdateField[ProvisioningVariant]
    capabilities: UpdateField[frozenset[TerminalCapabilities]]
    @classmethod
    def validate_port_in_range(cls, port: DontUpdate | int) -> DontUpdate | int: ...
    def validate_private_key(cls, private_key: UpdateField[CustomSecretStr], info: ValidationInfo) -> UpdateField[CustomSecretStr]: ...

class StoredNetconf(RADKitBaseModel):
    port: int
    username: str
    useInsecureAlgorithms: bool

class NewNetconf(RADKitBaseModel):
    port: int
    username: str
    password: AnnotatedCustomSecretStr
    useInsecureAlgorithms: bool
    @classmethod
    def validate_port_in_range(cls, port: int) -> int: ...

class UpdateNetconf(UpdateModel):
    port: UpdateField[int]
    username: UpdateField[str]
    password: UpdateField[AnnotatedCustomSecretStr]
    useInsecureAlgorithms: UpdateField[bool]
    @classmethod
    def validate_port_in_range(cls, port: DontUpdate | int) -> DontUpdate | int: ...

class StoredSNMP(RADKitBaseModel):
    version: int
    port: int

class NewSNMP(RADKitBaseModel):
    version: int
    port: int
    communityString: AnnotatedCustomSecretStr
    @classmethod
    def validate_port_in_range(cls, port: int) -> int: ...

class UpdateSNMP(UpdateModel):
    version: UpdateField[SNMPVersion]
    port: UpdateField[int]
    communityString: UpdateField[AnnotatedCustomSecretStr]
    @classmethod
    def validate_port_in_range(cls, port: DontUpdate | int) -> DontUpdate | int: ...

class StoredSwagger(RADKitBaseModel):
    schemaPath: str
    port: int
    username: str
    verify: bool | None
    useInsecureAlgorithms: bool

class NewSwagger(RADKitBaseModel):
    schemaPath: str
    port: int
    username: str
    password: AnnotatedCustomSecretStr
    verify: bool
    useInsecureAlgorithms: bool
    @classmethod
    def validate_port_in_range(cls, port: int) -> int: ...
    @classmethod
    def validate_schema_path_empty_or_starts_with_slash(cls, schemaPath: str) -> str: ...

class UpdateSwagger(UpdateModel):
    schemaPath: UpdateField[str]
    port: UpdateField[int]
    username: UpdateField[str]
    password: UpdateField[AnnotatedCustomSecretStr]
    verify: UpdateField[bool]
    useInsecureAlgorithms: UpdateField[bool]
    @classmethod
    def validate_port_in_range(cls, port: DontUpdate | int) -> DontUpdate | int: ...

class StoredHTTP(RADKitBaseModel):
    protocol: HTTPProtocol
    port: int
    username: str
    verify: bool
    useInsecureAlgorithms: bool
    authenticationExtra: str | None

class NewHTTP(RADKitBaseModel):
    protocol: HTTPProtocol
    port: int
    username: str
    password: AnnotatedCustomSecretStr
    verify: bool
    useInsecureAlgorithms: bool
    authenticationExtra: str | None
    def model_validator(self) -> Self: ...
    @classmethod
    def validate_port_in_range(cls, port: int) -> int: ...

class UpdateHTTP(UpdateModel):
    protocol: UpdateField[HTTPProtocol]
    port: UpdateField[int]
    username: UpdateField[str]
    password: UpdateField[AnnotatedCustomSecretStr]
    verify: UpdateField[bool]
    useInsecureAlgorithms: UpdateField[bool]
    authenticationExtra: UpdateField[str | None]
    @classmethod
    def validate_port_in_range(cls, port: DontUpdate | int) -> DontUpdate | int: ...

class StoredDeviceTemplateRef(RADKitBaseModel):
    deviceTemplateName: str
    deviceTemplateVariables: dict[str, str] | None

class NewDeviceTemplateRef(RADKitBaseModel):
    deviceTemplateName: str
    deviceTemplateVariables: dict[str, str]
    def check_key_value_constraints(cls, variables: dict[str, str]) -> dict[str, str]: ...

class UpdateDeviceTemplateRef(UpdateModel):
    deviceTemplateName: str
    deviceTemplateVariables: UpdateField[dict[str, str]]
    def check_key_value_constraints(cls, variables: UpdateField[dict[str, str]]) -> UpdateField[dict[str, str]]: ...

class MetaDataEntry(RADKitBaseModel):
    key: str
    value: str

class UpdateMetaDataSet(RADKitBaseModel):
    replace: Annotated[list[MetaDataEntry] | None, reject_duplicate_metadata]
    add: Annotated[list[MetaDataEntry], reject_duplicate_metadata]
    remove: list[str]
    @classmethod
    def check_metadata_replace_xor_add_remove(cls, values: dict[str, Any]) -> dict[str, Any]: ...
    def check_add_remove_are_distinct(self) -> Self: ...

class JumphostName(RADKitBaseModel):
    name: str

class StoredDevice(RADKitBaseModel):
    uuid: UUID4 | None
    name: str
    host: str
    deviceType: DeviceType
    jumphostRef: UUID4 | JumphostName | None
    enabled: bool
    forwardedTcpPorts: PortRanges
    labels: set[int]
    description: str
    sourceKey: str | None
    sourceDevUuid: UUID4 | None
    terminal: StoredTerminal | None
    netconf: StoredNetconf | None
    snmp: StoredSNMP | None
    swagger: StoredSwagger | None
    http: StoredHTTP | None
    deviceTemplateRef: StoredDeviceTemplateRef | None
    model_config: Incomplete

class StoredDevices(RADKitRootModel[list[StoredDevice]]):
    root: list[StoredDevice]

class StoredDeviceWithMetadata(StoredDevice):
    metaData: list[MetaDataEntry]
    model_config: Incomplete

class StoredDevicesWithMetadata(RADKitRootModel[list[StoredDeviceWithMetadata]]):
    root: list[StoredDeviceWithMetadata]

class DeviceSummary(RADKitBaseModel):
    uuid: UUID4 | None
    name: str | None
    host: str | None
    deviceType: DeviceType | None

class NewDevice(RADKitBaseModel):
    name: str
    host: str
    deviceType: DeviceType
    jumphostRef: UUID4 | JumphostName | None
    enabled: bool
    forwardedTcpPorts: PortRanges
    labels: Sequence[int | str]
    description: str
    sourceKey: str | None
    sourceDevUuid: UUID4 | None
    metaData: Annotated[list[MetaDataEntry], reject_duplicate_metadata]
    terminal: NewTerminal | None
    netconf: NewNetconf | None
    snmp: NewSNMP | None
    swagger: NewSwagger | None
    http: NewHTTP | None
    deviceTemplateRef: NewDeviceTemplateRef | None
    importGroup: str | None
    @classmethod
    def check_name_is_canonical(cls, name: str) -> str: ...
    @classmethod
    def validate_hostname(cls, hostname: str) -> str: ...
    def validate_provisioning_variant(self) -> Self: ...

class NewDevices(RADKitRootModel[list[NewDevice]]):
    root: Annotated[list[NewDevice], reject_duplicate_devices]
    model_config: Incomplete

class BaseUpdateDevice(RADKitBaseModel):
    name: UpdateField[NonEmptyString]
    host: UpdateField[NonEmptyString]
    deviceType: UpdateField[DeviceType]
    jumphostRef: UpdateField[UUID | None]
    enabled: UpdateField[bool]
    forwardedTcpPorts: UpdateField[PortRanges]
    labelUpdate: UpdateLabelSet
    description: UpdateField[str]
    sourceKey: UpdateField[str | None]
    sourceDevUuid: UpdateField[UUID | None]
    metaDataUpdate: UpdateMetaDataSet
    terminal: UpdateField[UpdateTerminal | None]
    netconf: UpdateField[UpdateNetconf | None]
    snmp: UpdateField[UpdateSNMP | None]
    swagger: UpdateField[UpdateSwagger | None]
    http: UpdateField[UpdateHTTP | None]
    deviceTemplateRef: UpdateField[UpdateDeviceTemplateRef | None]
    importGroup: UpdateField[str | None]
    def validate_provisioning_variant(self) -> Self: ...
    @classmethod
    def validate_name(cls, name: UpdateField[str]) -> UpdateField[str]: ...
    @classmethod
    def validate_hostname(cls, hostname: UpdateField[str]) -> UpdateField[str]: ...

class UpdateDevice(BaseUpdateDevice):
    uuid: UUID4
    model_config: Incomplete

class UpdateDevices(RADKitRootModel[list[UpdateDevice]]):
    root: list[UpdateDevice]
    model_config: Incomplete

class UpdateDevicesUniform(RADKitBaseModel):
    uuids: list[UUID4]
    update: BaseUpdateDevice

class DeviceUUIDs(RADKitRootModel[list[UUID4]]):
    root: list[UUID4]
    model_config: Incomplete
