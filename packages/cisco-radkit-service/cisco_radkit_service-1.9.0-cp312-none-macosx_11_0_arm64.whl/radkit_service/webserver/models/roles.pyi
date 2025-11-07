from .base import RADKitBaseModel, RADKitRootModel, UpdateField
from radkit_service.database import DbRole
from radkit_service.permissions import Claim
from typing import Any

__all__ = ['StoredRole', 'NewRole', 'NewRoles', 'UpdateRole', 'UpdateRoles', 'DeleteRoles']

class StoredRole(RADKitBaseModel):
    id: int
    name: str
    description: str
    claims: frozenset[Claim]
    readOnly: bool
    isSysadmin: bool
    @classmethod
    def from_db_role(cls, db_role: DbRole) -> StoredRole: ...

class NewRole(RADKitBaseModel):
    name: RoleName
    description: RoleDescription
    claims: frozenset[Claim]
    isSysadmin: bool

class NewRoles(RADKitRootModel[list[NewRole]]):
    root: list[NewRole]

class UpdateClaimSet(RADKitBaseModel):
    replace: frozenset[Claim] | None
    add: frozenset[Claim]
    remove: frozenset[Claim]
    @classmethod
    def check_claims_replace_xor_add_remove(cls, values: dict[str, Any]) -> dict[str, Any]: ...

class UpdateRole(RADKitBaseModel):
    id: int
    name: UpdateField[RoleName]
    description: UpdateField[RoleDescription]
    claimUpdate: UpdateClaimSet
    isSysadmin: UpdateField[bool]

class UpdateRoles(RADKitRootModel[list[UpdateRole]]):
    root: list[UpdateRole]

class DeleteRoles(RADKitRootModel[list[int]]):
    root: list[int]
