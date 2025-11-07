from .base import RADKitRootModel
from _typeshed import Incomplete
from pydantic import AnyHttpUrl
from radkit_common.types import AnnotatedCustomSecretStr, CustomSecretStr, ExternalSourceAuthenticationType, ExternalSourceType
from radkit_service.database.models import DbCyberArkCcp, DbCyberArkConjur, DbExternalSource, DbHashiCorpVault, DbKeyboardInteractiveChallenge, DbPlugin, DbStaticCredentials, DbStaticCredentialsMapping, DbStaticCredentialsMappingEntry, DbTacacsPlus
from radkit_service.external_sources.implementations.hashicorp_vault import SecretEngine
from radkit_service.webserver.models.base import DontUpdate, RADKitBaseModel, UpdateField
from typing import Literal
from uuid import UUID

__all__ = ['UpdateExternalSource', 'StoredExternalSources', 'NewExternalSource', 'DeleteExternalSources', 'NewKeyboardInteractiveChallenge', 'NewCyberArkConjur', 'UpdateKeyboardInteractiveChallenge', 'UpdateCyberArkConjur', 'NewTacacsPlus', 'UpdateTacacsPlus', 'NewCyberArkCcp', 'UpdateCyberArkCcp', 'StoredHashiCorpVault', 'NewHashiCorpVault', 'UpdateHashiCorpVault', 'NewHashiCorpVaultTokenAuth', 'NewHashiCorpVaultAppRoleAuth', 'UpdateHashiCorpVaultTokenAuth', 'UpdateHashiCorpVaultAppRoleAuth']

class StoredKeyboardInteractiveChallenge(RADKitBaseModel):
    type: Literal[ExternalSourceType.KEYBOARD_INTERACTIVE_CHALLENGE]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    username: str
    @classmethod
    def from_db_obj(cls, db_obj: DbKeyboardInteractiveChallenge) -> StoredKeyboardInteractiveChallenge: ...

class NewKeyboardInteractiveChallenge(RADKitBaseModel):
    type: Literal[ExternalSourceType.KEYBOARD_INTERACTIVE_CHALLENGE]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    username: str
    password: CustomSecretStr
    privateKey: CustomSecretStr
    privateKeyPassword: CustomSecretStr
    def validate_private_key(self) -> NewKeyboardInteractiveChallenge: ...

class UpdateKeyboardInteractiveChallenge(RADKitBaseModel):
    type: Literal[ExternalSourceType.KEYBOARD_INTERACTIVE_CHALLENGE]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    username: UpdateField[str]
    password: UpdateField[AnnotatedCustomSecretStr]
    privateKey: UpdateField[AnnotatedCustomSecretStr]
    privateKeyPassword: CustomSecretStr
    def validate_private_key(self) -> UpdateKeyboardInteractiveChallenge: ...

class StoredCyberArkConjur(RADKitBaseModel):
    type: Literal[ExternalSourceType.CYBERARK_CONJUR]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: AnyHttpUrl
    account: str
    username: str
    verify: bool
    useInsecureAlgorithms: bool
    @classmethod
    def from_db_obj(cls, db_obj: DbCyberArkConjur) -> StoredCyberArkConjur: ...

class NewCyberArkConjur(RADKitBaseModel):
    type: Literal[ExternalSourceType.CYBERARK_CONJUR]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: AnyHttpUrl
    account: str
    username: str
    apiKey: CustomSecretStr
    verify: bool
    useInsecureAlgorithms: bool

class UpdateCyberArkConjur(RADKitBaseModel):
    type: Literal[ExternalSourceType.CYBERARK_CONJUR]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: UpdateField[AnyHttpUrl]
    account: UpdateField[str]
    username: UpdateField[str]
    apiKey: UpdateField[AnnotatedCustomSecretStr]
    verify: UpdateField[bool]
    useInsecureAlgorithms: UpdateField[bool]

class StoredTacacsPlus(RADKitBaseModel):
    type: Literal[ExternalSourceType.TACACS_PLUS]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.ADMIN, ExternalSourceAuthenticationType.REMOTE_USER]]
    host: str
    port: int
    @classmethod
    def from_db_obj(cls, db_obj: DbTacacsPlus) -> StoredTacacsPlus: ...
    @classmethod
    def validate_hostname(cls, hostname: str) -> str: ...

class NewTacacsPlus(RADKitBaseModel):
    type: Literal[ExternalSourceType.TACACS_PLUS]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.ADMIN, ExternalSourceAuthenticationType.REMOTE_USER]]
    host: str
    port: int
    secret: CustomSecretStr
    @classmethod
    def validate_port_in_range(cls, port: int) -> int: ...

class UpdateTacacsPlus(RADKitBaseModel):
    type: Literal[ExternalSourceType.TACACS_PLUS]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.ADMIN, ExternalSourceAuthenticationType.REMOTE_USER]]
    host: UpdateField[str]
    port: UpdateField[int]
    secret: UpdateField[AnnotatedCustomSecretStr]
    @classmethod
    def validate_port_in_range(cls, port: DontUpdate | int) -> DontUpdate | int: ...

class StoredCyberArkCcp(RADKitBaseModel):
    type: Literal[ExternalSourceType.CYBERARK_CCP]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: AnyHttpUrl
    appId: str
    safe: str
    caCertificateChain: str
    certificate: str
    @classmethod
    def from_db_obj(cls, db_obj: DbCyberArkCcp) -> StoredCyberArkCcp: ...

class NewCyberArkCcp(RADKitBaseModel):
    type: Literal[ExternalSourceType.CYBERARK_CCP]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: AnyHttpUrl
    appId: str
    safe: str
    caCertificateChain: str
    certificate: str
    privateKey: CustomSecretStr
    privateKeyPassword: CustomSecretStr
    def validate_certificate(cls, value: str) -> str: ...
    def validate_entry(self) -> NewCyberArkCcp: ...

class UpdateCyberArkCcp(RADKitBaseModel):
    type: Literal[ExternalSourceType.CYBERARK_CCP]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: UpdateField[AnyHttpUrl]
    appId: UpdateField[str]
    safe: UpdateField[str]
    caCertificateChain: UpdateField[str]
    certificate: UpdateField[str]
    privateKey: UpdateField[AnnotatedCustomSecretStr]
    privateKeyPassword: CustomSecretStr
    def validate_certificate(cls, value: UpdateField[str]) -> UpdateField[str]: ...
    def validate_private_key(self) -> UpdateCyberArkCcp: ...

class NewStaticCredentials(RADKitBaseModel):
    type: Literal[ExternalSourceType.STATIC_CREDENTIALS]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    username: str
    password: CustomSecretStr

class UpdateStaticCredentials(RADKitBaseModel):
    type: Literal[ExternalSourceType.STATIC_CREDENTIALS]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    username: UpdateField[str]
    password: UpdateField[AnnotatedCustomSecretStr]

class StoredStaticCredentials(RADKitBaseModel):
    type: Literal[ExternalSourceType.STATIC_CREDENTIALS]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    username: str
    @classmethod
    def from_db_obj(cls, db_obj: DbStaticCredentials) -> StoredStaticCredentials: ...

class NewStaticCredentialsMappingEntry(RADKitBaseModel):
    remote_user: str
    username: str
    password: CustomSecretStr
    is_regex: bool
    def validate_entry(self) -> NewStaticCredentialsMappingEntry: ...

class NewStaticCredentialsMapping(RADKitBaseModel):
    type: Literal[ExternalSourceType.STATIC_CREDENTIALS_MAPPING]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    entries: list[NewStaticCredentialsMappingEntry]
    @classmethod
    def validate_entries_duplicates(cls, entries: list[NewStaticCredentialsMappingEntry]) -> list[NewStaticCredentialsMappingEntry]: ...

class UpdateStaticCredentialsMappingEntry(RADKitBaseModel):
    uuid: UUID | None
    remote_user: UpdateField[str]
    username: UpdateField[str]
    password: UpdateField[AnnotatedCustomSecretStr]
    is_regex: UpdateField[bool]
    def validate_entry(self) -> UpdateStaticCredentialsMappingEntry: ...

class UpdateStaticCredentialsMapping(RADKitBaseModel):
    type: Literal[ExternalSourceType.STATIC_CREDENTIALS_MAPPING]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    entries: list[UpdateStaticCredentialsMappingEntry]
    @classmethod
    def validate_entries_duplicates(cls, entries: DontUpdate | list[NewStaticCredentialsMappingEntry]) -> DontUpdate | list[NewStaticCredentialsMappingEntry]: ...

class StoredStaticCredentialsMappingEntry(RADKitBaseModel):
    uuid: UUID
    remote_user: str
    username: str
    is_regex: bool
    @classmethod
    def from_db_obj(cls, db_obj: DbStaticCredentialsMappingEntry) -> StoredStaticCredentialsMappingEntry: ...

class StoredStaticCredentialsMapping(RADKitBaseModel):
    type: Literal[ExternalSourceType.STATIC_CREDENTIALS_MAPPING]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    entries: list[StoredStaticCredentialsMappingEntry]
    @classmethod
    def from_db_obj(cls, db_obj: DbStaticCredentialsMapping) -> StoredStaticCredentialsMapping: ...

class NewPlugin(RADKitBaseModel):
    type: Literal[ExternalSourceType.PLUGIN]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE, ExternalSourceAuthenticationType.ADMIN, ExternalSourceAuthenticationType.REMOTE_USER]]
    pluginName: str
    @classmethod
    def check_existence_of_plugin(cls, plugin_name: str) -> str: ...
    @classmethod
    def from_db_obj(cls, db_obj: DbPlugin) -> NewPlugin: ...

class UpdatePlugin(RADKitBaseModel):
    type: Literal[ExternalSourceType.PLUGIN]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE, ExternalSourceAuthenticationType.ADMIN, ExternalSourceAuthenticationType.REMOTE_USER]]
    pluginName: UpdateField[str]
    @classmethod
    def from_db_obj(cls, db_obj: DbPlugin) -> UpdatePlugin: ...

class StoredPlugin(RADKitBaseModel):
    type: Literal[ExternalSourceType.PLUGIN]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE, ExternalSourceAuthenticationType.ADMIN, ExternalSourceAuthenticationType.REMOTE_USER]]
    pluginName: str
    @classmethod
    def from_db_obj(cls, db_obj: DbPlugin) -> StoredPlugin: ...

class StoredHashiCorpVaultAuth(RADKitBaseModel):
    method: Literal['token', 'approle']
    path: str

class StoredHashiCorpVault(RADKitBaseModel):
    type: Literal[ExternalSourceType.HASHICORP_VAULT]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: AnyHttpUrl
    engine: SecretEngine
    enginePath: str
    auth: StoredHashiCorpVaultAuth
    verify: bool
    useInsecureAlgorithms: bool
    @classmethod
    def from_db_obj(cls, db_obj: DbHashiCorpVault) -> StoredHashiCorpVault: ...

class NewHashiCorpVaultTokenAuth(RADKitBaseModel):
    method: Literal['token']
    path: str
    token: CustomSecretStr

class NewHashiCorpVaultAppRoleAuth(RADKitBaseModel):
    method: Literal['approle']
    path: str
    roleId: CustomSecretStr
    secretId: CustomSecretStr

class NewHashiCorpVault(RADKitBaseModel):
    type: Literal[ExternalSourceType.HASHICORP_VAULT]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: AnyHttpUrl
    engine: SecretEngine
    enginePath: str
    auth: NewHashiCorpVaultTokenAuth | NewHashiCorpVaultAppRoleAuth
    verify: bool
    useInsecureAlgorithms: bool

class UpdateHashiCorpVaultTokenAuth(RADKitBaseModel):
    method: Literal['token']
    path: str
    token: UpdateField[AnnotatedCustomSecretStr]

class UpdateHashiCorpVaultAppRoleAuth(RADKitBaseModel):
    method: Literal['approle']
    path: str
    roleId: UpdateField[AnnotatedCustomSecretStr]
    secretId: UpdateField[AnnotatedCustomSecretStr]

class UpdateHashiCorpVault(RADKitBaseModel):
    type: Literal[ExternalSourceType.HASHICORP_VAULT]
    authentication_types: set[Literal[ExternalSourceAuthenticationType.DEVICE]]
    baseUrl: UpdateField[AnyHttpUrl]
    engine: UpdateField[SecretEngine]
    enginePath: UpdateField[str]
    auth: UpdateField[UpdateHashiCorpVaultTokenAuth | UpdateHashiCorpVaultAppRoleAuth]
    verify: UpdateField[bool]
    useInsecureAlgorithms: UpdateField[bool]

class StoredExternalSources(RADKitBaseModel):
    name: str
    options: StoredKeyboardInteractiveChallenge | StoredCyberArkConjur | StoredCyberArkCcp | StoredTacacsPlus | StoredStaticCredentials | StoredStaticCredentialsMapping | StoredPlugin | StoredHashiCorpVault
    @classmethod
    def from_db_external_sources(cls, external_source: DbExternalSource) -> StoredExternalSources: ...

class NewExternalSource(RADKitBaseModel):
    name: str
    options: NewKeyboardInteractiveChallenge | NewCyberArkConjur | NewCyberArkCcp | NewTacacsPlus | NewStaticCredentials | NewStaticCredentialsMapping | NewPlugin | NewHashiCorpVault

class UpdateExternalSource(RADKitBaseModel):
    name: str
    options: UpdateKeyboardInteractiveChallenge | UpdateCyberArkConjur | UpdateCyberArkCcp | UpdateTacacsPlus | UpdateStaticCredentials | UpdateStaticCredentialsMapping | UpdatePlugin | UpdateHashiCorpVault

class DeleteExternalSources(RADKitRootModel[list[str]]):
    root: list[str]
    model_config: Incomplete
