# core/models/structure.py

from enum import Enum

from pydantic import Field

from reveal.core.providers.models.common import CoreModel


class StructureValueType(str, Enum):
    """Observed Python value types."""

    NULL = "null"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    OBJECT = "object"
    ARRAY = "array"


class StructureNode(CoreModel):
    """Structural information about one logical path."""

    path: str
    kind: StructureValueType
    occurrences: int = 0
    null_count: int = 0
    value_types: set[StructureValueType] = Field(
        default_factory=set
    )

    min_value: float | None = None
    max_value: float | None = None

    min_length: int | None = None
    max_length: int | None = None


class StructureModel(CoreModel):
    """Structural analysis of a DocumentNode tree."""
    nodes: list[StructureNode] = Field(
        default_factory=list
    )
    total_nodes: int = 0
    total_values: int = 0
