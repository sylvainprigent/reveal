from enum import Enum

from pydantic import Field

from reveal.core.providers.models.common import CoreModel


class RelationalType(str, Enum):
    """Database-independent relational data types."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    STRING = "string"
    TEXT = "text"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    JSON = "json"
    BINARY = "binary"


class ColumnNullability(str, Enum):
    """Nullability of a relational column."""

    NULLABLE = "nullable"
    REQUIRED = "required"


class RelationshipType(str, Enum):
    """Cardinality of a relationship."""

    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"


class ColumnModel(CoreModel):
    """A database-independent relational column."""

    name: str
    relational_type: RelationalType
    nullable: ColumnNullability = (
        ColumnNullability.NULLABLE
    )
    primary_key: bool = False
    unique: bool = False
    source_path: str | None = None
    confidence: float = 1.0


class ForeignKeyModel(CoreModel):
    """A foreign-key relationship between two tables."""

    column: str
    referenced_table: str
    referenced_column: str
    relationship_type: RelationshipType
    confidence: float = 1.0


class TableModel(CoreModel):
    """A database-independent relational table."""

    name: str
    source_path: str
    columns: list[ColumnModel] = Field(
        default_factory=list
    )
    foreign_keys: list[ForeignKeyModel] = Field(
        default_factory=list
    )


class RelationalModel(CoreModel):
    """Database-independent relational schema."""

    tables: list[TableModel] = Field(
        default_factory=list
    )
