from typing import Any

from rich.console import Console
from rich.tree import Tree

from reveal.core.providers.models.enums import NodeKind
from reveal.core.providers.models.node import DocumentNode


def print_document_node(
    node: DocumentNode,
    *,
    console: Console | None = None,
) -> None:
    """Display a DocumentNode as a colored terminal tree."""
    console = console or Console()

    tree = Tree(
        _format_node(node),
        guide_style="dim",
    )

    _add_children(tree, node)

    console.print(tree)


def _add_children(
    tree: Tree,
    node: DocumentNode,
) -> None:
    for child in node.children:
        child_tree = tree.add(
            _format_node(child)
        )
        _add_children(child_tree, child)


def _format_node(node: DocumentNode) -> str:

    if node.kind == NodeKind.VALUE:
        return (
            f"[cyan]{node.name}[/cyan] "
            f"[dim]VALUE[/dim]: "
            f"[green]{node.value!r}[/green]"
        )

    if node.kind == NodeKind.ARRAY:
        label = (
            f"[yellow]{node.name}[/yellow] "
            if node.name
            else ""
        )
        return f"{label}[bold yellow]ARRAY[/bold yellow]"

    label = (
        f"[magenta]{node.name}[/magenta] "
        if node.name
        else ""
    )

    return f"{label}[bold magenta]OBJECT[/bold magenta]"