from pydantic import BaseModel
from radkit_common.settings import Pedigree, ResolveResult
from typing import Annotated, Any, Literal

__all__ = ['SettingChange']

class SettingChange(BaseModel):
    setting: str
    layers: list[Literal['toml', 'api']]
    value: Any
    remove: bool

class APISettingInfo(BaseModel):
    setting: str
    effective_value: Annotated[Any, None]
    type: str
    value_source: Literal['default', 'toml', 'env', 'cli', 'api']
    description: str
    api_writable: bool
    api_persistent: bool
    webui_visible: bool
    layer_values: dict[Pedigree, Annotated[Any, None]]
    layer_errors: dict[Pedigree, str]
    @classmethod
    def from_resolve_result(cls, resolve_result: ResolveResult[Any]) -> APISettingInfo: ...
