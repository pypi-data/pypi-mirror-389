from typing import (
    Type,
    Dict,
    Tuple,
    List,
    Iterable
)

from pydantic import BaseModel
from pydantic.fields import FieldInfo as PydanticFieldInfo

from sqlmodel import SQLModel
from sqlmodel.main import FieldInfo as SqlModelFieldInfo


def get_fields(
        model_cls: Type[BaseModel | SQLModel],
        exclude_fields: Iterable[str] = None,
        include_fields: Iterable[str] = None
) -> Dict[str, Tuple[Type, PydanticFieldInfo | SqlModelFieldInfo]]:
    exclude_fields = exclude_fields or []
    fields = {
        name: (info.annotation, info)
        for name, info in model_cls.model_fields.items()
        if name not in exclude_fields
    }
    if include_fields:
        fields = {name: fields[name] for name in include_fields}
    return fields
