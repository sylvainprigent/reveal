from __future__ import annotations

from typing import Any

from reveal.core.content.models import (
    NodeKind,
    DocumentNode
)
from reveal.core.structure.models import (
    StructureModel,
    StructureNode,
    StructureValueType,
)


class StructureAnalyzer:
    """Analyze and normalize the structure of a DocumentNode tree.

    The analyzer produces a logical structural representation rather
    than simply reproducing the physical tree.

    In particular, it recognizes both explicit arrays::

        {
            "recipes": [
                {"title": "Cake"},
                {"title": "Soup"}
            ]
        }

    and implicit collections represented by numeric object keys::

        {
            "0": {"title": "Cake"},
            "1": {"title": "Soup"}
        }

    Both structures are represented as::

        $.recipes[]
        $.recipes[].title

    or, for the second example::

        $[]
        $[].title
    """

    def analyze(self, root: DocumentNode) -> StructureModel:
        """Analyze a document tree.

        Args:
            root: Root DocumentNode.

        Returns:
            A StructureModel containing the normalized structure.
        """
        nodes: dict[str, StructureNode] = {}

        self._walk(
            node=root,
            path="$",
            nodes=nodes,
        )

        total_values = sum(
            node.occurrences
            for node in nodes.values()
            if node.kind
            in {
                StructureValueType.NULL,
                StructureValueType.BOOLEAN,
                StructureValueType.INTEGER,
                StructureValueType.FLOAT,
                StructureValueType.STRING,
            }
        )

        return StructureModel(
            nodes=list(nodes.values()),
            total_nodes=len(nodes),
            total_values=total_values,
        )

    def _walk(
        self,
        node: DocumentNode,
        path: str,
        nodes: dict[str, StructureNode],
    ) -> None:
        """Recursively walk a DocumentNode."""

        if node.kind == NodeKind.VALUE:
            self._record_value(
                path=path,
                value=node.value,
                nodes=nodes,
            )
            return

        if node.kind == NodeKind.ARRAY:
            self._record_container(
                path=path,
                kind=StructureValueType.ARRAY,
                nodes=nodes,
            )

            for child in node.children:
                self._walk(
                    node=child,
                    path=f"{path}[]",
                    nodes=nodes,
                )

            return

        if node.kind == NodeKind.OBJECT:
            # An object whose children are numeric keys and whose
            # children are themselves objects is very often an
            # implicit collection:
            #
            # {
            #     "0": {...},
            #     "1": {...}
            # }
            if self._is_implicit_collection(node):
                collection_path = f"{path}[]"

                for child in node.children:
                    self._walk(
                        node=child,
                        path=collection_path,
                        nodes=nodes,
                    )

                return

            self._record_container(
                path=path,
                kind=StructureValueType.OBJECT,
                nodes=nodes,
            )

            for child in node.children:
                child_path = self._build_child_path(
                    path=path,
                    child=child,
                )

                self._walk(
                    node=child,
                    path=child_path,
                    nodes=nodes,
                )

    def _record_value(
        self,
        *,
        path: str,
        value: Any,
        nodes: dict[str, StructureNode],
    ) -> None:
        """Record a value and update its statistics."""

        value_type = self._get_value_type(value)

        current = nodes.get(path)

        if current is None:
            nodes[path] = StructureNode(
                path=path,
                kind=value_type,
                occurrences=1,
                null_count=1 if value is None else 0,
                value_types={value_type},
                min_value=self._numeric_value(value),
                max_value=self._numeric_value(value),
                min_length=self._value_length(value),
                max_length=self._value_length(value),
            )
            return

        numeric_value = self._numeric_value(value)
        value_length = self._value_length(value)

        min_value = current.min_value
        max_value = current.max_value

        if numeric_value is not None:
            if min_value is None:
                min_value = numeric_value
            else:
                min_value = min(min_value, numeric_value)

            if max_value is None:
                max_value = numeric_value
            else:
                max_value = max(max_value, numeric_value)

        min_length = current.min_length
        max_length = current.max_length

        if value_length is not None:
            if min_length is None:
                min_length = value_length
            else:
                min_length = min(min_length, value_length)

            if max_length is None:
                max_length = value_length
            else:
                max_length = max(max_length, value_length)

        nodes[path] = current.model_copy(
            update={
                "occurrences": current.occurrences + 1,
                "null_count": current.null_count
                + (1 if value is None else 0),
                "value_types": current.value_types | {value_type},
                "min_value": min_value,
                "max_value": max_value,
                "min_length": min_length,
                "max_length": max_length,
            }
        )

    def _record_container(
        self,
        *,
        path: str,
        kind: StructureValueType,
        nodes: dict[str, StructureNode],
    ) -> None:
        """Record an object or array container."""

        current = nodes.get(path)

        if current is None:
            nodes[path] = StructureNode(
                path=path,
                kind=kind,
                occurrences=1,
            )
            return

        nodes[path] = current.model_copy(
            update={
                "occurrences": current.occurrences + 1,
            }
        )

    @staticmethod
    def _build_child_path(
        *,
        path: str,
        child: DocumentNode,
    ) -> str:
        """Build the canonical path for an object child."""

        if child.name is None:
            return path

        if path == "$":
            return f"$.{child.name}"

        return f"{path}.{child.name}"

    @staticmethod
    def _is_implicit_collection(
        node: DocumentNode,
    ) -> bool:
        """Detect an object representing an implicit collection.

        The MVP heuristic requires:

        * at least two children;
        * every child has a numeric name;
        * every child is an OBJECT.

        For example::

            {
                "0": {"name": "Alice"},
                "1": {"name": "Bob"}
            }

        is interpreted as a collection of objects.
        """

        if len(node.children) < 2:
            return False

        return all(
            child.name is not None
            and child.name.isdigit()
            and child.kind == NodeKind.OBJECT
            for child in node.children
        )

    @staticmethod
    def _get_value_type(
        value: Any,
    ) -> StructureValueType:
        """Return the structural type of a Python value."""

        if value is None:
            return StructureValueType.NULL

        if isinstance(value, bool):
            return StructureValueType.BOOLEAN

        if isinstance(value, int):
            return StructureValueType.INTEGER

        if isinstance(value, float):
            return StructureValueType.FLOAT

        if isinstance(value, str):
            return StructureValueType.STRING

        return StructureValueType.OBJECT

    @staticmethod
    def _numeric_value(
        value: Any,
    ) -> float | None:
        """Return a numeric value suitable for statistics."""

        if isinstance(value, bool):
            return None

        if isinstance(value, int | float):
            return float(value)

        return None

    @staticmethod
    def _value_length(
        value: Any,
    ) -> int | None:
        """Return the length of a value when meaningful."""

        if isinstance(value, str):
            return len(value)

        return None