from rich.console import Console
from rich.table import Table

from reveal.core.semantic.models import (
    SemanticModel,
    SemanticNode,
)


def print_semantic_model(
    model: SemanticModel,
    *,
    console: Console | None = None,
) -> None:
    """Display a SemanticModel as a readable terminal table.

    Args:
        model: Semantic analysis result to display.
        console: Optional Rich console. A new console is created when
            omitted.
    """
    console = console or Console()

    table = Table(
        title="Semantic Analysis",
        show_header=True,
        header_style="bold",
    )

    table.add_column("Path", style="cyan")
    table.add_column("Semantic Type", style="magenta")
    table.add_column("Confidence", justify="right")
    table.add_column("Format")
    table.add_column("Pattern")
    table.add_column("Evidence")

    for node in model.nodes:
        table.add_row(
            node.path,
            _semantic_type(node),
            _confidence(node.confidence),
            node.format or "",
            node.pattern or "",
            _evidence(node),
        )

    console.print(table)

    console.print(
        f"\nNodes: {model.total_nodes} | "
        f"Classified: {model.classified_nodes}"
    )


def _semantic_type(node: SemanticNode) -> str:
    if hasattr(node.semantic_type, "value"):
        return str(node.semantic_type.value)

    return str(node.semantic_type)


def _confidence(confidence: float) -> str:
    return f"{confidence:.0%}"


def _evidence(node: SemanticNode) -> str:
    if not node.evidence:
        return ""

    return ", ".join(
        evidence.description
        for evidence in node.evidence
    )
