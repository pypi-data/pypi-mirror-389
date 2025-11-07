from _typeshed import Incomplete
from pydantic import computed_field
from pydantic_core import ErrorDetails
from radkit_service.database.models import DbDeviceTemplate, DbVariableDefinition
from radkit_service.webserver.models.base import RADKitBaseModel, RADKitRootModel, UpdateField

__all__ = ['StoredDeviceTemplate', 'NewDeviceTemplate', 'DeleteDeviceTemplates', 'UpdateDeviceTemplate', 'NewVariableDefinition']

class StoredVariableDefinition(RADKitBaseModel):
    name: str
    description: str
    defaultValue: str | None
    @classmethod
    def from_db_variable_definition(cls, db_variable_definition: DbVariableDefinition) -> StoredVariableDefinition: ...

class StoredDeviceTemplate(RADKitBaseModel):
    name: str
    description: str
    variableDefinitions: list[StoredVariableDefinition]
    protocolsDefinitionTemplate: str
    isValid: bool
    @computed_field
    def warnings(self) -> list[str]: ...
    @classmethod
    def from_db_device_template(cls, db_device_template: DbDeviceTemplate, external_source_names: set[str] | None = None) -> StoredDeviceTemplate: ...

class NewVariableDefinition(RADKitBaseModel):
    name: str
    description: str
    default_value: str | None

class ValidateDeviceTemplateResult(RADKitBaseModel):
    success: bool
    errors: list[ErrorDetails]

class NewDeviceTemplate(RADKitBaseModel):
    name: str
    description: str
    variable_definitions: list[NewVariableDefinition]
    protocols_definition_template: str

class UpdateDeviceTemplate(RADKitBaseModel):
    name: str
    description: UpdateField[str]
    variable_definitions: UpdateField[list[NewVariableDefinition]]
    protocols_definition_template: str

class DeleteDeviceTemplates(RADKitRootModel[list[str]]):
    root: list[str]
    model_config: Incomplete
