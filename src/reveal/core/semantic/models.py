from enum import Enum

from reveal.core.common.models import CoreModel


class SemanticType(str, Enum):
    """Semantic type inferred for a field."""

    UNKNOWN = "unknown"

    TEXT = "text"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    NUMBER = "number"

    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"

    EMAIL = "email"
    URL = "url"

    IDENTIFIER = "identifier"

    PERCENTAGE = "percentage"
    CURRENCY = "currency"

    CATEGORY = "category"


class SemanticEvidenceType(str, Enum):
    """Type of evidence used for semantic inference."""

    FIELD_NAME = "field_name"
    VALUE_PATTERN = "value_pattern"
    VALUE_TYPE = "value_type"
    VALUE_DISTRIBUTION = "value_distribution"


class SemanticEvidence(CoreModel):
    """Evidence supporting a semantic inference."""

    type: SemanticEvidenceType
    description: str
    score: float


class SemanticNode(CoreModel):
    """Semantic interpretation of one logical data path."""

    path: str

    semantic_type: SemanticType = SemanticType.UNKNOWN

    confidence: float = 0.0

    format: str | None = None
    pattern: str | None = None

    evidence: list[SemanticEvidence] = []


class SemanticModel(CoreModel):
    """Semantic analysis of a document structure."""

    nodes: list[SemanticNode] = []

    total_nodes: int = 0
    classified_nodes: int = 0