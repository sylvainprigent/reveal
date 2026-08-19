import re
from collections.abc import Iterable

from reveal.core.content.models import DocumentNode
from reveal.core.semantic.models import (
    SemanticEvidence,
    SemanticEvidenceType,
    SemanticModel,
    SemanticNode,
    SemanticType,
)
from reveal.core.structure.models import (
    StructureModel,
    StructureNode,
    StructureValueType,
)


class SemanticAnalyzer:
    """Infer semantic meaning from structural information.

    This MVP uses simple deterministic heuristics based on:

    - field names
    - observed value types
    - observed value patterns

    The analyzer is intentionally conservative. When there is not
    enough evidence, the semantic type remains UNKNOWN.
    """

    DATE_PATTERNS = (
        (
            re.compile(r"^\d{4}-\d{2}-\d{2}$"),
            "%Y-%m-%d",
        ),
        (
            re.compile(r"^\d{4}/\d{2}/\d{2}$"),
            "%Y/%m/%d",
        ),
        (
            re.compile(r"^\d{2}/\d{2}/\d{4}$"),
            "%d/%m/%Y",
        ),
    )

    DATETIME_PATTERNS = (
        (
            re.compile(
                r"^\d{4}-\d{2}-\d{2}"
                r"[T ]\d{2}:\d{2}:\d{2}"
            ),
            "%Y-%m-%dT%H:%M:%S",
        ),
    )

    EMAIL_PATTERN = re.compile(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    URL_PATTERN = re.compile(
        r"^https?://[^\s]+$",
        re.IGNORECASE,
    )

    def analyze(
        self,
        node: DocumentNode,
        structure: StructureModel,
    ) -> SemanticModel:
        """Analyze a StructureModel and infer semantic types.
        
        DocumentNode is here for future use, now the sémantic analyzer is dumb on purpose

        """

        nodes = [
            self._analyze_node(node)
            for node in structure.nodes
        ]

        classified_nodes = sum(
            node.semantic_type != SemanticType.UNKNOWN
            for node in nodes
        )

        return SemanticModel(
            nodes=nodes,
            total_nodes=len(nodes),
            classified_nodes=classified_nodes,
        )

    def _analyze_node(
        self,
        node: StructureNode,
    ) -> SemanticNode:
        field_name = self._field_name(node.path)

        if self._is_date_candidate(node):
            return self._date_node(node, field_name)

        if self._is_datetime_candidate(node):
            return self._datetime_node(node, field_name)

        if self._is_email_candidate(node):
            return self._email_node(node, field_name)

        if self._is_url_candidate(node):
            return self._url_node(node, field_name)

        if self._is_identifier_candidate(node, field_name):
            return self._identifier_node(node, field_name)

        if StructureValueType.BOOLEAN in node.value_types:
            return SemanticNode(
                path=node.path,
                semantic_type=SemanticType.BOOLEAN,
                confidence=1.0,
                evidence=[
                    SemanticEvidence(
                        type=SemanticEvidenceType.VALUE_TYPE,
                        description="Observed boolean values.",
                        score=1.0,
                    )
                ],
            )

        if StructureValueType.INTEGER in node.value_types:
            return SemanticNode(
                path=node.path,
                semantic_type=SemanticType.INTEGER,
                confidence=1.0,
                evidence=[
                    SemanticEvidence(
                        type=SemanticEvidenceType.VALUE_TYPE,
                        description="Observed integer values.",
                        score=1.0,
                    )
                ],
            )

        if (
            StructureValueType.INTEGER in node.value_types
            or StructureValueType.FLOAT in node.value_types
        ):
            return SemanticNode(
                path=node.path,
                semantic_type=SemanticType.NUMBER,
                confidence=1.0,
                evidence=[
                    SemanticEvidence(
                        type=SemanticEvidenceType.VALUE_TYPE,
                        description="Observed numeric values.",
                        score=1.0,
                    )
                ],
            )

        if StructureValueType.STRING in node.value_types:
            return SemanticNode(
                path=node.path,
                semantic_type=SemanticType.TEXT,
                confidence=0.5,
                evidence=[
                    SemanticEvidence(
                        type=SemanticEvidenceType.VALUE_TYPE,
                        description="Observed string values.",
                        score=0.5,
                    )
                ],
            )

        return SemanticNode(path=node.path)

    def _is_date_candidate(
        self,
        node: StructureNode,
    ) -> bool:
        if StructureValueType.STRING not in node.value_types:
            return False

        return self._name_contains(
            node.path,
            "date",
        )

    def _date_node(
        self,
        node: StructureNode,
        field_name: str,
    ) -> SemanticNode:
        evidence = [
            SemanticEvidence(
                type=SemanticEvidenceType.FIELD_NAME,
                description=(
                    f"Field name '{field_name}' suggests a date."
                ),
                score=0.7,
            )
        ]

        pattern, date_format = self._detect_pattern(
            node
        )

        confidence = 0.7

        if pattern is not None:
            evidence.append(
                SemanticEvidence(
                    type=SemanticEvidenceType.VALUE_PATTERN,
                    description=(
                        "Observed values match a known date pattern."
                    ),
                    score=0.95,
                )
            )
            confidence = 0.95

        return SemanticNode(
            path=node.path,
            semantic_type=SemanticType.DATE,
            confidence=confidence,
            format=date_format,
            pattern=pattern,
            evidence=evidence,
        )

    def _is_datetime_candidate(
        self,
        node: StructureNode,
    ) -> bool:
        if StructureValueType.STRING not in node.value_types:
            return False

        return self._name_contains(
            node.path,
            "datetime",
            "timestamp",
            "created_at",
            "updated_at",
        )

    def _datetime_node(
        self,
        node: StructureNode,
        field_name: str,
    ) -> SemanticNode:
        evidence = [
            SemanticEvidence(
                type=SemanticEvidenceType.FIELD_NAME,
                description=(
                    f"Field name '{field_name}' suggests a datetime."
                ),
                score=0.7,
            )
        ]

        for regex, date_format in self.DATETIME_PATTERNS:
            # At this stage we only have StructureModel information.
            # Pattern confirmation will be added when the structure
            # model retains sampled values.
            return SemanticNode(
                path=node.path,
                semantic_type=SemanticType.DATETIME,
                confidence=0.7,
                format=date_format,
                pattern=regex.pattern,
                evidence=evidence,
            )

        return SemanticNode(
            path=node.path,
            semantic_type=SemanticType.DATETIME,
            confidence=0.7,
            evidence=evidence,
        )

    def _is_email_candidate(
        self,
        node: StructureNode,
    ) -> bool:
        return (
            StructureValueType.STRING in node.value_types
            and self._name_contains(node.path, "email", "e-mail")
        )

    def _email_node(
        self,
        node: StructureNode,
        field_name: str,
    ) -> SemanticNode:
        return SemanticNode(
            path=node.path,
            semantic_type=SemanticType.EMAIL,
            confidence=0.8,
            pattern=self.EMAIL_PATTERN.pattern,
            evidence=[
                SemanticEvidence(
                    type=SemanticEvidenceType.FIELD_NAME,
                    description=(
                        f"Field name '{field_name}' suggests an email."
                    ),
                    score=0.8,
                )
            ],
        )

    def _is_url_candidate(
        self,
        node: StructureNode,
    ) -> bool:
        return (
            StructureValueType.STRING in node.value_types
            and self._name_contains(
                node.path,
                "url",
                "uri",
                "link",
            )
        )

    def _url_node(
        self,
        node: StructureNode,
        field_name: str,
    ) -> SemanticNode:
        return SemanticNode(
            path=node.path,
            semantic_type=SemanticType.URL,
            confidence=0.8,
            pattern=self.URL_PATTERN.pattern,
            evidence=[
                SemanticEvidence(
                    type=SemanticEvidenceType.FIELD_NAME,
                    description=(
                        f"Field name '{field_name}' suggests a URL."
                    ),
                    score=0.8,
                )
            ],
        )

    def _is_identifier_candidate(
        self,
        node: StructureNode,
        field_name: str,
    ) -> bool:
        return (
            self._name_contains(
                field_name,
                "id",
                "identifier",
                "uuid",
            )
            and (
                StructureValueType.STRING in node.value_types
                or StructureValueType.INTEGER in node.value_types
            )
        )

    def _identifier_node(
        self,
        node: StructureNode,
        field_name: str,
    ) -> SemanticNode:
        return SemanticNode(
            path=node.path,
            semantic_type=SemanticType.IDENTIFIER,
            confidence=0.75,
            evidence=[
                SemanticEvidence(
                    type=SemanticEvidenceType.FIELD_NAME,
                    description=(
                        f"Field name '{field_name}' suggests an identifier."
                    ),
                    score=0.75,
                )
            ],
        )

    def _detect_pattern(
        self,
        node: StructureNode,
    ) -> tuple[str | None, str | None]:
        """Return a matching date regex and format.

        The current StructureModel does not contain individual values,
        so this method only provides the hook for value-based detection.

        Once sampled values are added to the structure layer, this can
        test what percentage of values match each pattern.
        """

        return None, None

    @staticmethod
    def _field_name(path: str) -> str:
        if not path:
            return ""

        path = path.rstrip("[]")

        if "." in path:
            return path.rsplit(".", 1)[-1]

        return path

    @staticmethod
    def _name_contains(
        name: str,
        *terms: str,
    ) -> bool:
        normalized = name.lower()

        return any(
            term.lower() in normalized
            for term in terms
        )
