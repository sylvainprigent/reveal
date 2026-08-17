from __future__ import annotations

from collections.abc import Iterable

from reveal.core.providers.models.enums import NodeKind
from reveal.core.providers.models.node import DocumentNode
from reveal.core.relational.models import (
    ColumnModel,
    ColumnNullability,
    ForeignKeyModel,
    RelationalModel,
    RelationalType,
    RelationshipType,
    TableModel,
)
from reveal.core.semantic.models import SemanticModel
from reveal.core.structure.models import (
    StructureModel,
    StructureValueType,
)


class RelationalMapper:
    """Map a document tree to a database-independent relational schema.

    MVP mapping rules:

    OBJECT
        scalar children -> columns
        OBJECT child -> child table + FK
        ARRAY of scalars -> child table + FK + display_order
        ARRAY of objects -> child table + FK + object fields + display_order

    Additionally, an OBJECT whose children are multiple OBJECT nodes
    with a compatible structure is interpreted as a collection of
    objects. Those objects become rows of a single table.
    """

    def map(
        self,
        root: DocumentNode,
        structure: StructureModel,
        semantic: SemanticModel,
    ) -> RelationalModel:
        """Map a document into a relational schema.

        ``structure`` and ``semantic`` are intentionally part of the
        public API even though the MVP only uses a small amount of
        structural information. Future versions will use them for
        type inference, identifiers, relationships and semantic
        normalization.
        """
        tables: list[TableModel] = []

        # Keep these arguments in the API for future semantic mapping.
        # The MVP currently derives the schema directly from the tree.
        del structure
        del semantic

        if root.kind != NodeKind.OBJECT:
            raise ValueError(
                "Relational mapping requires an OBJECT root."
            )

        if self._is_object_collection(root):
            self._map_object_collection(
                root=root,
                tables=tables,
            )
        else:
            self._map_single_object(
                node=root,
                table_name=self._table_name(
                    root.name or "document"
                ),
                parent_table=None,
                tables=tables,
            )

        return RelationalModel(tables=tables)

    # ------------------------------------------------------------------
    # Collection detection
    # ------------------------------------------------------------------

    def _is_object_collection(
        self,
        node: DocumentNode,
    ) -> bool:
        """Return True when an object represents a collection.

        The current DocumentNode representation commonly represents a
        top-level JSON array as:

            OBJECT
            ├── 0 OBJECT
            ├── 1 OBJECT
            └── 2 OBJECT

        If there are at least two object children and they have
        compatible fields, we interpret them as rows of one table.
        """
        object_children = [
            child
            for child in node.children
            if child.kind == NodeKind.OBJECT
        ]

        if len(object_children) < 2:
            return False

        signatures = [
            self._object_signature(child)
            for child in object_children
        ]

        if not signatures:
            return False

        # MVP: require a compatible structure.
        first = signatures[0]

        return all(
            self._compatible_signatures(first, signature)
            for signature in signatures[1:]
        )

    @staticmethod
    def _object_signature(
        node: DocumentNode,
    ) -> frozenset[str]:
        """Return the set of direct field names of an object."""
        return frozenset(
            child.name
            for child in node.children
            if child.name is not None
        )

    @staticmethod
    def _compatible_signatures(
        left: frozenset[str],
        right: frozenset[str],
    ) -> bool:
        """Determine whether two objects have compatible structures.

        For the MVP we allow missing fields. This is important for
        semi-structured data where records may not contain exactly the
        same fields.
        """
        if not left or not right:
            return False

        common = left & right

        # Require meaningful overlap.
        smaller = min(len(left), len(right))

        return len(common) / smaller >= 0.5

    # ------------------------------------------------------------------
    # Object collection
    # ------------------------------------------------------------------

    def _map_object_collection(
        self,
        root: DocumentNode,
        tables: list[TableModel],
    ) -> None:
        """Map a collection of objects to one parent table."""
        objects = [
            child
            for child in root.children
            if child.kind == NodeKind.OBJECT
        ]

        table_name = self._infer_collection_table_name(root)

        table = TableModel(
            name=table_name,
            source_path="$",
            columns=[
                ColumnModel(
                    name="id",
                    relational_type=RelationalType.INTEGER,
                    nullable=ColumnNullability.REQUIRED,
                    primary_key=True,
                )
            ],
        )

        tables.append(table)

        # Collect the union of all scalar fields.
        fields = self._collect_object_fields(objects)

        for field_name, field_node in fields.items():
            if field_node.kind != NodeKind.VALUE:
                continue

            table.columns.append(
                ColumnModel(
                    name=self._column_name(field_name),
                    relational_type=self._relational_type(
                        field_node
                    ),
                    nullable=ColumnNullability.NULLABLE,
                    source_path=field_name,
                )
            )

        # Nested structures are mapped once from the collection,
        # not once per object.
        nested_fields = self._collect_nested_fields(objects)

        for field_name, nodes in nested_fields.items():
            representative = nodes[0]

            if representative.kind == NodeKind.ARRAY:
                self._map_collection_array(
                    field_name=field_name,
                    nodes=nodes,
                    parent_table=table,
                    tables=tables,
                )

            elif representative.kind == NodeKind.OBJECT:
                self._map_collection_object(
                    field_name=field_name,
                    nodes=nodes,
                    parent_table=table,
                    tables=tables,
                )

    def _collect_object_fields(
        self,
        objects: Iterable[DocumentNode],
    ) -> dict[str, DocumentNode]:
        """Collect the union of scalar/object/array fields."""
        fields: dict[str, DocumentNode] = {}

        for obj in objects:
            for child in obj.children:
                if child.name is None:
                    continue

                fields.setdefault(
                    child.name,
                    child,
                )

        return fields

    def _collect_nested_fields(
        self,
        objects: Iterable[DocumentNode],
    ) -> dict[str, list[DocumentNode]]:
        """Collect nested fields across all collection objects."""
        fields: dict[str, list[DocumentNode]] = {}

        for obj in objects:
            for child in obj.children:
                if child.name is None:
                    continue

                if child.kind in (
                    NodeKind.OBJECT,
                    NodeKind.ARRAY,
                ):
                    fields.setdefault(
                        child.name,
                        [],
                    ).append(child)

        return fields

    # ------------------------------------------------------------------
    # Normal object mapping
    # ------------------------------------------------------------------

    def _map_single_object(
        self,
        node: DocumentNode,
        table_name: str,
        parent_table: TableModel | None,
        tables: list[TableModel],
    ) -> TableModel:
        """Map one OBJECT node to one table."""
        table = TableModel(
            name=table_name,
            source_path=node.name or "$",
            columns=[
                ColumnModel(
                    name="id",
                    relational_type=RelationalType.INTEGER,
                    nullable=ColumnNullability.REQUIRED,
                    primary_key=True,
                )
            ],
        )

        tables.append(table)

        if parent_table is not None:
            fk = self._foreign_key_name(parent_table.name)

            table.columns.append(
                ColumnModel(
                    name=fk,
                    relational_type=RelationalType.INTEGER,
                    nullable=ColumnNullability.REQUIRED,
                )
            )

            table.foreign_keys.append(
                ForeignKeyModel(
                    column=fk,
                    referenced_table=parent_table.name,
                    referenced_column="id",
                    relationship_type=(
                        RelationshipType.MANY_TO_ONE
                    ),
                )
            )

        for child in node.children:
            self._map_object_child(
                child=child,
                parent_table=table,
                tables=tables,
            )

        return table

    def _map_object_child(
        self,
        child: DocumentNode,
        parent_table: TableModel,
        tables: list[TableModel],
    ) -> None:
        """Map a direct child of an object."""
        if child.kind == NodeKind.VALUE:
            if child.name is None:
                return

            parent_table.columns.append(
                ColumnModel(
                    name=self._column_name(child.name),
                    relational_type=self._relational_type(child),
                    nullable=ColumnNullability.NULLABLE,
                    source_path=child.name,
                )
            )
            return

        if child.kind == NodeKind.OBJECT:
            self._map_single_object(
                node=child,
                table_name=self._unique_table_name(
                    self._table_name(child.name or "object"),
                    tables,
                ),
                parent_table=parent_table,
                tables=tables,
            )
            return

        if child.kind == NodeKind.ARRAY:
            self._map_array(
                child=child,
                parent_table=parent_table,
                tables=tables,
            )

    # ------------------------------------------------------------------
    # Nested structures of collection
    # ------------------------------------------------------------------

    def _map_collection_array(
        self,
        field_name: str,
        nodes: list[DocumentNode],
        parent_table: TableModel,
        tables: list[TableModel],
    ) -> None:
        """Map an array field belonging to a collection."""
        elements = [
            element
            for node in nodes
            for element in node.children
        ]

        if not elements:
            return

        if all(
            element.kind == NodeKind.VALUE
            for element in elements
        ):
            self._create_scalar_array_table(
                name=f"{parent_table.name}_{field_name}",
                source_path=field_name,
                representative=elements[0],
                parent_table=parent_table,
                tables=tables,
            )
            return

        if all(
            element.kind == NodeKind.OBJECT
            for element in elements
        ):
            self._create_object_array_table(
                name=f"{parent_table.name}_{field_name}",
                source_path=field_name,
                elements=elements,
                parent_table=parent_table,
                tables=tables,
            )

    def _map_collection_object(
        self,
        field_name: str,
        nodes: list[DocumentNode],
        parent_table: TableModel,
        tables: list[TableModel],
    ) -> None:
        """Map an OBJECT field shared by collection records."""
        representative = next(
            (
                node
                for node in nodes
                if node.kind == NodeKind.OBJECT
            ),
            None,
        )

        if representative is None:
            return

        table_name = self._unique_table_name(
            self._table_name(field_name),
            tables,
        )

        self._map_single_object(
            node=representative,
            table_name=table_name,
            parent_table=parent_table,
            tables=tables,
        )

    # ------------------------------------------------------------------
    # Arrays
    # ------------------------------------------------------------------

    def _map_array(
        self,
        child: DocumentNode,
        parent_table: TableModel,
        tables: list[TableModel],
    ) -> None:
        """Map an ARRAY belonging to one object."""
        if child.name is None or not child.children:
            return

        kinds = {
            element.kind
            for element in child.children
        }

        table_name = self._unique_table_name(
            self._table_name(
                f"{parent_table.name}_{child.name}"
            ),
            tables,
        )

        if kinds == {NodeKind.VALUE}:
            self._create_scalar_array_table(
                name=table_name,
                source_path=child.name,
                representative=child.children[0],
                parent_table=parent_table,
                tables=tables,
            )
            return

        if kinds == {NodeKind.OBJECT}:
            self._create_object_array_table(
                name=table_name,
                source_path=child.name,
                elements=child.children,
                parent_table=parent_table,
                tables=tables,
            )

    def _create_scalar_array_table(
        self,
        name: str,
        source_path: str,
        representative: DocumentNode,
        parent_table: TableModel,
        tables: list[TableModel],
    ) -> None:
        """Create a table for an array of scalar values."""
        fk = self._foreign_key_name(parent_table.name)

        tables.append(
            TableModel(
                name=self._unique_table_name(name, tables),
                source_path=source_path,
                columns=[
                    ColumnModel(
                        name="id",
                        relational_type=RelationalType.INTEGER,
                        nullable=ColumnNullability.REQUIRED,
                        primary_key=True,
                    ),
                    ColumnModel(
                        name=fk,
                        relational_type=RelationalType.INTEGER,
                        nullable=ColumnNullability.REQUIRED,
                    ),
                    ColumnModel(
                        name="value",
                        relational_type=self._relational_type(
                            representative
                        ),
                        nullable=ColumnNullability.NULLABLE,
                    ),
                    ColumnModel(
                        name="display_order",
                        relational_type=RelationalType.INTEGER,
                        nullable=ColumnNullability.REQUIRED,
                    ),
                ],
                foreign_keys=[
                    ForeignKeyModel(
                        column=fk,
                        referenced_table=parent_table.name,
                        referenced_column="id",
                        relationship_type=(
                            RelationshipType.MANY_TO_ONE
                        ),
                    )
                ],
            )
        )

    def _create_object_array_table(
        self,
        name: str,
        source_path: str,
        elements: list[DocumentNode],
        parent_table: TableModel,
        tables: list[TableModel],
    ) -> None:
        """Create a table for an array of objects."""
        fk = self._foreign_key_name(parent_table.name)

        table = TableModel(
            name=self._unique_table_name(name, tables),
            source_path=source_path,
            columns=[
                ColumnModel(
                    name="id",
                    relational_type=RelationalType.INTEGER,
                    nullable=ColumnNullability.REQUIRED,
                    primary_key=True,
                ),
                ColumnModel(
                    name=fk,
                    relational_type=RelationalType.INTEGER,
                    nullable=ColumnNullability.REQUIRED,
                ),
                ColumnModel(
                    name="display_order",
                    relational_type=RelationalType.INTEGER,
                    nullable=ColumnNullability.REQUIRED,
                ),
            ],
            foreign_keys=[
                ForeignKeyModel(
                    column=fk,
                    relational_type=RelationalType.INTEGER,
                    referenced_table=parent_table.name,
                    referenced_column="id",
                    relationship_type=(
                        RelationshipType.MANY_TO_ONE
                    ),
                )
            ],
        )

        tables.append(table)

        fields = self._collect_object_fields(elements)

        for field_name, field in fields.items():
            if field.kind != NodeKind.VALUE:
                continue

            table.columns.append(
                ColumnModel(
                    name=self._column_name(field_name),
                    relational_type=self._relational_type(field),
                    nullable=ColumnNullability.NULLABLE,
                    source_path=field_name,
                )
            )

    # ------------------------------------------------------------------
    # Type and naming helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _relational_type(
        node: DocumentNode,
    ) -> RelationalType:
        """Infer a relational type from a document value."""
        value = node.value

        if value is None:
            return RelationalType.STRING

        if isinstance(value, bool):
            return RelationalType.BOOLEAN

        if isinstance(value, int):
            return RelationalType.INTEGER

        if isinstance(value, float):
            return RelationalType.FLOAT

        return RelationalType.STRING

    @staticmethod
    def _table_name(name: str) -> str:
        return (
            name.strip()
            .lower()
            .replace(" ", "_")
        )

    @staticmethod
    def _column_name(name: str) -> str:
        return (
            name.strip()
            .lower()
            .replace(" ", "_")
        )

    @staticmethod
    def _foreign_key_name(
        parent_table_name: str,
    ) -> str:
        return f"{parent_table_name}_id"

    @staticmethod
    def _unique_table_name(
        name: str,
        tables: list[TableModel],
    ) -> str:
        existing = {
            table.name
            for table in tables
        }

        if name not in existing:
            return name

        index = 2

        while f"{name}_{index}" in existing:
            index += 1

        return f"{name}_{index}"

    @staticmethod
    def _infer_collection_table_name(
        root: DocumentNode,
    ) -> str:
        """Infer the table name for a top-level collection."""
        # A root JSON array represented as OBJECT has no useful name.
        # For the MVP use "document".
        #
        # This can later use SemanticModel to infer e.g. "recipe".
        return "document"