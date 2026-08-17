from reveal.core.providers.models.node import DocumentNode
from reveal.core.quality.models import (
    QualityIssue,
    QualityIssueType,
    QualityModel,
    QualityNode,
    QualitySeverity,
)
from reveal.core.semantic.models import (
    SemanticModel,
    SemanticType,
)
from reveal.core.structure.models import StructureModel


class DataQualityAnalyzer:
    """Analyze data quality using structural and semantic information.

    This is an MVP implementation based entirely on aggregated
    StructureModel and SemanticModel information.

    The analyzer does not modify the original document.
    """

    def analyze(
        self,
        document_node: DocumentNode,
        structure: StructureModel,
        semantic: SemanticModel | None = None,
    ) -> QualityModel:
        """Analyze data quality.

        Args:
            structure: Structural analysis of the document.
            semantic: Optional semantic analysis.

        Returns:
            A QualityModel containing quality scores and issues.
        """

        semantic_nodes = {}

        if semantic is not None:
            semantic_nodes = {
                node.path: node
                for node in semantic.nodes
            }

        quality_nodes: list[QualityNode] = []
        all_issues: list[QualityIssue] = []

        for structure_node in structure.nodes:
            issues = self._analyze_structure_node(
                structure_node,
                semantic_nodes.get(structure_node.path),
            )

            score = self._calculate_score(
                structure_node,
                issues,
            )

            quality_node = QualityNode(
                path=structure_node.path,
                score=score,
                issues=issues,
            )

            quality_nodes.append(quality_node)
            all_issues.extend(issues)

        affected_nodes = sum(
            bool(node.issues)
            for node in quality_nodes
        )

        dataset_score = self._calculate_dataset_score(
            quality_nodes
        )

        return QualityModel(
            score=dataset_score,
            nodes=quality_nodes,
            issues=all_issues,
            total_nodes=len(quality_nodes),
            affected_nodes=affected_nodes,
            total_issues=len(all_issues),
        )

    def _analyze_structure_node(
        self,
        node,
        semantic_node,
    ) -> list[QualityIssue]:
        issues: list[QualityIssue] = []

        if node.null_count > 0:
            issues.append(
                self._null_issue(node)
            )

        if len(node.value_types) > 1:
            non_null_types = {
                value_type
                for value_type in node.value_types
                if value_type.value != "null"
            }

            if len(non_null_types) > 1:
                issues.append(
                    self._mixed_type_issue(node)
                )

        if semantic_node is not None:
            issues.extend(
                self._semantic_issues(
                    node,
                    semantic_node,
                )
            )

        return issues

    @staticmethod
    def _null_issue(node) -> QualityIssue:
        return QualityIssue(
            path=node.path,
            issue_type=QualityIssueType.NULL_VALUES,
            severity=QualitySeverity.WARNING,
            message=(
                f"{node.null_count} of "
                f"{node.occurrences} occurrences are null."
            ),
            occurrences=node.occurrences,
            affected_occurrences=node.null_count,
        )

    @staticmethod
    def _mixed_type_issue(node) -> QualityIssue:
        types = ", ".join(
            sorted(
                value_type.value
                for value_type in node.value_types
                if value_type.value != "null"
            )
        )

        return QualityIssue(
            path=node.path,
            issue_type=QualityIssueType.MIXED_TYPES,
            severity=QualitySeverity.WARNING,
            message=(
                f"Field contains multiple value types: {types}."
            ),
            occurrences=node.occurrences,
            affected_occurrences=node.occurrences,
        )

    @staticmethod
    def _semantic_issues(
        structure_node,
        semantic_node,
    ) -> list[QualityIssue]:
        issues: list[QualityIssue] = []

        if (
            semantic_node.semantic_type
            == SemanticType.UNKNOWN
        ):
            return issues

        if semantic_node.confidence < 0.5:
            issues.append(
                QualityIssue(
                    path=structure_node.path,
                    issue_type=QualityIssueType.LOW_CONFIDENCE,
                    severity=QualitySeverity.INFO,
                    message=(
                        "Semantic classification has low confidence."
                    ),
                    occurrences=structure_node.occurrences,
                    confidence=semantic_node.confidence,
                )
            )

        return issues

    @staticmethod
    def _calculate_score(
        node,
        issues: list[QualityIssue],
    ) -> float:
        if not issues:
            return 1.0

        score = 1.0

        for issue in issues:
            if issue.issue_type == QualityIssueType.NULL_VALUES:
                if node.occurrences:
                    ratio = (
                        issue.affected_occurrences
                        / node.occurrences
                    )

                    score -= ratio * 0.5

            elif issue.issue_type == QualityIssueType.MIXED_TYPES:
                score -= 0.3

            elif issue.issue_type == QualityIssueType.SEMANTIC_FORMAT:
                score -= 0.4

            elif issue.issue_type == QualityIssueType.LOW_CONFIDENCE:
                score -= 0.05

        return max(0.0, min(1.0, score))

    @staticmethod
    def _calculate_dataset_score(
        nodes: list[QualityNode],
    ) -> float:
        if not nodes:
            return 1.0

        return sum(
            node.score
            for node in nodes
        ) / len(nodes)
