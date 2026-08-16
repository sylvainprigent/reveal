

from reveal.core.structure.models import StructureModel


def print_structure_model(
    structure: StructureModel,
) -> None:
    for node in structure.nodes:
        kind = (
            node.kind.value
            if hasattr(node.kind, "value")
            else str(node.kind)
        )

        types = [
            value_type.value
            if hasattr(value_type, "value")
            else str(value_type)
            for value_type in node.value_types
        ]

        print(
            f"{node.path}: "
            f"{kind} "
            f"occurrences={node.occurrences} "
            f"nulls={node.null_count} "
            f"types={types}"
        )