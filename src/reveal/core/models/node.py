

from enum import Enum
from typing import Any

from pydantic import Field

from reveal.core.models.common import CoreModel
from reveal.core.models.enums import NodeKind



class DocumentNode(CoreModel):
    kind: NodeKind
    name: str | None = None
    value: Any | None = None
    children: list["DocumentNode"] = Field(
        default_factory=list
    )
