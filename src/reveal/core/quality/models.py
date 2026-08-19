from enum import Enum

from pydantic import Field

from reveal.core.common.models import CoreModel


class QualitySeverity(str, Enum):
    """Severity of a data quality issue."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QualityIssueType(str, Enum):
    """Type of data quality issue."""

    NULL_VALUES = "null_values"
    MIXED_TYPES = "mixed_types"
    SEMANTIC_FORMAT = "semantic_format"
    LOW_CONFIDENCE = "low_confidence"


class QualityIssue(CoreModel):
    """A single data quality issue."""

    path: str
    issue_type: QualityIssueType
    severity: QualitySeverity

    message: str

    occurrences: int = 0
    affected_occurrences: int = 0

    confidence: float | None = None


class QualityNode(CoreModel):
    """Quality information for one logical path."""
    path: str
    score: float = 1.0
    issues: list[QualityIssue] = Field(
        default_factory=list
    )


class QualityModel(CoreModel):
    """Data quality analysis of a document."""

    score: float = 1.0
    nodes: list[QualityNode] = Field(
        default_factory=list
    )
    issues: list[QualityIssue] = Field(
        default_factory=list
    )
    total_nodes: int = 0
    affected_nodes: int = 0
    total_issues: int = 0
