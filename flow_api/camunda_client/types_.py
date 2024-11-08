from enum import Enum
from typing import Annotated, Any, Literal, TypeAlias, TypeVar, Optional, Dict

from pydantic import BaseModel, BeforeValidator, ConfigDict


def _snake_to_camel(string: str) -> str:
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=_snake_to_camel,
    )


class BaseDTO(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


_T = TypeVar("_T", bound=BaseSchema)


def _validate_nullable_list(value: list[_T] | None) -> list[_T]:
    if value is None:
        return []
    return value


MayBeNullableList = Annotated[list[_T], BeforeValidator(_validate_nullable_list)]
OptionalDict: TypeAlias = dict[str, Any] | None
class VariableTypes(str, Enum):
    BOOLEAN = "Boolean"
    BYTES = "Bytes"
    SHORT = "Short"
    INTEGER = "Integer"
    LONG = "Long"
    DOUBLE = "Double"
    DATE = "Date"
    STRING = "String"
    NULL = "Null"
    OBJECT = "Object"
    JSON = "Json"


class VariableValueSchema(BaseSchema):
    value: Any  # This field is required and must be present
    type: str
    label: str | None = None
    value_info: Optional[Dict[str, Any]] = None


VariablesFixed: TypeAlias = dict[str, dict]

Variables: TypeAlias = dict[str, VariableValueSchema]

TVariables = TypeVar("TVariables", bound=BaseModel)
