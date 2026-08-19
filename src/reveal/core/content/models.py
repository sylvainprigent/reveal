from enum import Enum
from typing import Any

from pydantic import Field

from reveal.core.common.models import CoreModel


class NodeKind(str, Enum):
    OBJECT = "object"
    ARRAY = "array"
    VALUE = "value"


class DocumentNode(CoreModel):
    kind: NodeKind
    name: str | None = None
    value: Any | None = None
    children: list["DocumentNode"] = Field(
        default_factory=list
    )
