from enum import Enum


class SourceType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"


class NodeKind(str, Enum):
    OBJECT = "object"
    ARRAY = "array"
    VALUE = "value"


class LogicalType(str, Enum):
    UNKNOWN = "unknown"
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    ENUM = "enum"
    IDENTIFIER = "identifier"


class RelationshipType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class IssueCategory(str, Enum):
    STRUCTURE = "structure"
    TYPE = "type"
    MISSING_VALUE = "missing_value"
    DUPLICATE = "duplicate"
    RELATIONSHIP = "relationship"


class NormalizationStrategy(str, Enum):
    WIDE = "wide"
    NORMALIZED = "normalized"
    EAV = "entity_attribute_value"
