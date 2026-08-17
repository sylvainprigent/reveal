from rich.console import Console
from rich.tree import Tree

from reveal.core.relational.models import (
    ColumnModel,
    ForeignKeyModel,
    RelationalModel,
    TableModel,
)


def print_relational_model(
    model: RelationalModel,
    *,
    console: Console | None = None,
) -> None:
    """Display a RelationalModel as a colored terminal tree."""
    console = console or Console()

    foreign_key_count = sum(
        len(table.foreign_keys)
        for table in model.tables
    )

    tree = Tree(
        (
            "[bold magenta]RELATIONAL MODEL[/bold magenta] "
            f"[dim]({len(model.tables)} tables, "
            f"{foreign_key_count} foreign keys)[/dim]"
        ),
        guide_style="dim",
    )

    for table in model.tables:
        _add_table(tree, table)

    console.print(tree)


def _add_table(
    tree: Tree,
    table: TableModel,
) -> None:
    """Add a table and its columns."""
    table_tree = tree.add(
        _format_table(table)
    )

    for column in table.columns:
        table_tree.add(
            _format_column(column)
        )

    if table.foreign_keys:
        foreign_keys_tree = table_tree.add(
            "[bold cyan]FOREIGN KEYS[/bold cyan]"
        )

        for foreign_key in table.foreign_keys:
            foreign_keys_tree.add(
                _format_foreign_key(foreign_key)
            )


def _format_table(
    table: TableModel,
) -> str:
    """Format a table."""
    return (
        f"[bold yellow]TABLE[/bold yellow] "
        f"[cyan]{table.name}[/cyan] "
        f"[dim]← {table.source_path}[/dim]"
    )


def _format_column(
    column: ColumnModel,
) -> str:
    """Format a relational column."""
    parts = [
        f"[green]{column.name}[/green]",
        f"[dim]{_enum_value(column.relational_type)}[/dim]",
    ]

    if column.primary_key:
        parts.append(
            "[bold yellow]PK[/bold yellow]"
        )

    if column.unique:
        parts.append(
            "[bold blue]UNIQUE[/bold blue]"
        )

    nullable = _enum_value(column.nullable)

    if nullable == "required":
        parts.append(
            "[bold red]NOT NULL[/bold red]"
        )
    else:
        parts.append(
            "[dim]NULL[/dim]"
        )

    if column.confidence < 1.0:
        parts.append(
            f"[dim]confidence={column.confidence:.0%}[/dim]"
        )

    return " ".join(parts)


def _format_foreign_key(
    foreign_key: ForeignKeyModel,
) -> str:
    """Format a foreign key."""
    relationship_type = _enum_value(
        foreign_key.relationship_type
    )

    return (
        f"[cyan]{foreign_key.column}[/cyan] "
        "[bold blue]→[/bold blue] "
        f"[cyan]{foreign_key.referenced_table}"
        f".{foreign_key.referenced_column}[/cyan] "
        f"[dim]({relationship_type})[/dim]"
    )


def _enum_value(value: object) -> str:
    """Return an enum value or a string representation."""
    enum_value = getattr(value, "value", None)

    if enum_value is not None:
        return str(enum_value)

    return str(value)
