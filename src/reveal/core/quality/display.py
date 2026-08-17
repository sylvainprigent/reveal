from rich.console import Console
from rich.table import Table

from reveal.core.quality.models import (
    QualityIssue,
    QualityModel,
    QualitySeverity,
)


def print_quality_model(
    model: QualityModel,
    *,
    console: Console | None = None,
) -> None:
    """Display a QualityModel as a readable terminal report.

    Args:
        model: Data quality analysis result.
        console: Optional Rich console.
    """
    console = console or Console()

    console.print()
    console.print("[bold]Data Quality Analysis[/bold]")
    console.print()

    table = Table(
        show_header=True,
        header_style="bold",
    )

    table.add_column("Path", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Issues", justify="right")
    table.add_column("Status")

    for node in model.nodes:
        table.add_row(
            node.path,
            _format_score(node.score),
            str(len(node.issues)),
            _format_status(node.score),
        )

    console.print(table)

    console.print()

    console.print(
        f"[bold]Overall score:[/bold] "
        f"{_format_score(model.score)}"
    )

    console.print(
        f"[bold]Nodes:[/bold] {model.total_nodes}    "
        f"[bold]Affected:[/bold] {model.affected_nodes}    "
        f"[bold]Issues:[/bold] {model.total_issues}"
    )

    if model.issues:
        console.print()
        console.print("[bold]Issues[/bold]")
        console.print()

        _print_issues(
            model.issues,
            console=console,
        )


def _format_score(score: float) -> str:
    if score >= 0.95:
        return f"[green]{score:.1%}[/green]"

    if score >= 0.80:
        return f"[yellow]{score:.1%}[/yellow]"

    return f"[red]{score:.1%}[/red]"


def _format_status(score: float) -> str:
    if score >= 0.95:
        return "[green]GOOD[/green]"

    if score >= 0.80:
        return "[yellow]WARNING[/yellow]"

    return "[red]BAD[/red]"


def _print_issues(
    issues: list[QualityIssue],
    *,
    console: Console,
) -> None:
    table = Table(
        show_header=True,
        header_style="bold",
    )

    table.add_column("Severity")
    table.add_column("Path", style="cyan")
    table.add_column("Type")
    table.add_column("Message")
    table.add_column("Affected", justify="right")

    for issue in issues:
        table.add_row(
            _format_severity(issue.severity),
            issue.path,
            _format_issue_type(issue),
            issue.message,
            str(issue.affected_occurrences),
        )

    console.print(table)


def _format_severity(
    severity: QualitySeverity,
) -> str:
    if severity == QualitySeverity.ERROR:
        return "[red]ERROR[/red]"

    if severity == QualitySeverity.WARNING:
        return "[yellow]WARNING[/yellow]"

    return "[blue]INFO[/blue]"


def _format_issue_type(issue: QualityIssue) -> str:
    return issue.issue_type.value