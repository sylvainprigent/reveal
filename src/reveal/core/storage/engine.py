from typing import Any

from reveal.core.content.models import DocumentNode, NodeKind
from reveal.core.document.models import DocumentMetadata
from reveal.core.quality.models import QualityModel
from reveal.core.relational.models import ColumnModel, ColumnNullability, ForeignKeyModel, RelationalModel, TableModel
from reveal.core.semantic.models import SemanticModel
from reveal.core.storage.interfaces import StorageBackend
from reveal.core.storage.models import StorageColumn, StorageForeignKey
from reveal.core.structure.models import StructureModel


class StorageGenerator:
    """
    Generic database materializer.

    Contains all database-independent persistence logic.
    Concrete storage concerns are delegated to StorageBackend.
    """

    def __init__(
        self,
        backend: StorageBackend,
    ) -> None:
        self.backend = backend

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def create_schema(
        self,
        model: RelationalModel,
    ) -> None:

        self.backend.open()

        try:
            for table in model.tables:
                columns = [
                    StorageColumn(
                        name=column.name,
                        type=column.relational_type,
                        nullable=column.nullable
                        == ColumnNullability.NULLABLE,
                        primary_key=column.primary_key,
                        unique=column.unique,
                    )
                    for column in table.columns
                ]

                foreign_keys = [
                    StorageForeignKey(
                        column=fk.column,
                        referenced_table=fk.referenced_table,
                        referenced_column=fk.referenced_column,
                    )
                    for fk in table.foreign_keys
                ]

                self.backend.create_table(
                    name=table.name,
                    columns=columns,
                    foreign_keys=foreign_keys,
                )

            self.backend.commit()

        except Exception:
            self.backend.rollback()
            raise

        finally:
            self.backend.close()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def load_data(
        self,
        root: DocumentNode,
        model: RelationalModel,
    ) -> None:

        self.backend.open()

        try:
            root_table = self._find_root_table(model)
            print("root table=", root_table)

            self._load_root(
                root=root,
                table=root_table,
                model=model,
            )

            self.backend.commit()

        except Exception:
            self.backend.rollback()
            raise

        finally:
            self.backend.close()

    def _find_root_table(
        self,
        model: RelationalModel,
    ) -> TableModel:
        """
        Find the root table.

        The mapper uses '$' as the root source path.
        """

        for table in model.tables:
            if table.source_path == "$":
                return table

        # Defensive fallback: first table.
        if model.tables:
            return model.tables[0]

        raise ValueError(
            "RelationalModel contains no tables."
        )

    def _find_child_table(
        self,
        model: RelationalModel,
        parent_table: TableModel,
        child_name: str,
    ) -> TableModel | None:
        """
        Find the table representing a child of `parent_table`.

        The mapper normally stores source paths such as:

            ingredients
            instructions
            nutrients

        and for nested paths:

            ingredients[].something
        """

        candidates = []

        parent_path = parent_table.source_path

        for table in model.tables:
            if table is parent_table:
                continue

            source = table.source_path

            if self._source_matches_child(
                parent_path,
                source,
                child_name,
            ):
                candidates.append(table)

        if not candidates:
            return None

        # Prefer the shortest / most direct match.
        candidates.sort(
            key=lambda table: len(
                table.source_path
            )
        )

        return candidates[0]

    @staticmethod
    def _source_matches_child(
        parent_path: str,
        child_path: str,
        child_name: str,
    ) -> bool:
        """
        Determine whether a relational source path represents
        a direct child of the current object.

        Examples:

            parent '$'
            child 'ingredients'
            -> True

            parent '$[]'
            child 'ingredients'
            -> True

            parent '$'
            child '$.ingredients'
            -> True

            parent '$[]'
            child '$[].ingredients'
            -> True
        """

        normalized_parent = parent_path.rstrip(".")

        # Simple mapper paths.
        if child_path == child_name:
            return True

        # Root-relative paths.
        expected_paths = {
            f"{normalized_parent}.{child_name}",
            f"{normalized_parent}{child_name}",
        }

        if child_path in expected_paths:
            return True

        # Collection root.
        if normalized_parent == "$":
            if child_path == f"$.{child_name}":
                return True

            if child_path == child_name:
                return True

        if normalized_parent == "$[]":
            if child_path == f"$[].{child_name}":
                return True

            if child_path == child_name:
                return True

        return False

    def _load_root(
        self,
        root: DocumentNode,
        table: TableModel,
        model: RelationalModel,
    ) -> None:

        kind = self._kind(root)
        if kind == NodeKind.ARRAY:
            for index, child in enumerate(root.children):

                if self._kind(child) != NodeKind.OBJECT:
                    continue

                self._load_object(
                    node=child,
                    table=table,
                    model=model,
                    parent_table=None,
                    parent_id=None,
                    display_order=index,
                )

            return

        if kind == NodeKind.OBJECT:

            if self._is_object_collection(root):
                for index, child in enumerate(root.children):

                    self._load_object(
                        node=child,
                        table=table,
                        model=model,
                        parent_table=None,
                        parent_id=None,
                        display_order=index,
                    )

                return

            # Normal single object.
            self._load_object(
                node=root,
                table=table,
                model=model,
                parent_table=None,
                parent_id=None,
                display_order=None,
            )

            return

        raise ValueError(
            "The document root must be an OBJECT or ARRAY."
        )

    def _load_object(
        self,
        node: DocumentNode,
        table: TableModel,
        model: RelationalModel,
        parent_table: TableModel | None,
        parent_id: Any | None,
        display_order: int | None,
    ) -> Any:

        values: dict[str, Any] = {}

        # Parent FK
        if parent_table is not None:
            fk = self._find_parent_fk(
                table,
                parent_table,
            )

            if fk is not None:
                values[fk.column] = parent_id

        # display_order
        if display_order is not None:
            column = self._find_column(
                table,
                "display_order",
            )

            if column is not None:
                values[column.name] = display_order

        # Scalar fields
        for child in node.children:

            if self._kind(child) != NodeKind.VALUE:
                continue

            if child.name is None:
                continue

            column = self._find_column(
                table,
                child.name,
            )

            if column is not None:
                values[column.name] = child.value

        row_id = self.backend.insert(
            table=table.name,
            values=values,
        )

        self._load_children(
            node=node,
            parent_table=table,
            parent_id=row_id,
            model=model,
        )

        return row_id

    def _load_array(
        self,
        array_node: DocumentNode,
        parent_table: TableModel,
        parent_id: Any,
        model: RelationalModel,
    ) -> None:

        if array_node.name is None:
            return

        child_table = self._find_child_table(
            model=model,
            parent_table=parent_table,
            child_name=array_node.name,
        )

        if child_table is None:
            return

        for index, element in enumerate(
            array_node.children
        ):

            # ["foo", "bar", "baz"]
            if self._kind(element) == NodeKind.VALUE:

                values: dict[str, Any] = {}

                fk = self._find_parent_fk(
                    child_table,
                    parent_table,
                )

                if fk is not None:
                    values[fk.column] = parent_id

                value_column = self._find_value_column(
                    child_table
                )

                if value_column is not None:
                    values[value_column.name] = element.value

                order_column = self._find_column(
                    child_table,
                    "display_order",
                )

                if order_column is not None:
                    values[order_column.name] = index

                self.backend.insert(
                    table=child_table.name,
                    values=values,
                )

            # [{"x": 1}, {"x": 2}]
            elif self._kind(element) == NodeKind.OBJECT:

                self._load_object(
                    node=element,
                    table=child_table,
                    model=model,
                    parent_table=parent_table,
                    parent_id=parent_id,
                    display_order=index,
                )

    def _load_children(
        self,
        node: DocumentNode,
        parent_table: TableModel,
        parent_id: Any,
        model: RelationalModel,
    ) -> None:

        for child in node.children:

            if child.name is None:
                continue

            kind = self._kind(child)

            if kind == NodeKind.OBJECT:

                child_table = self._find_child_table(
                    model=model,
                    parent_table=parent_table,
                    child_name=child.name,
                )

                if child_table is None:
                    continue

                self._load_object(
                    node=child,
                    table=child_table,
                    model=model,
                    parent_table=parent_table,
                    parent_id=parent_id,
                    display_order=None,
                )

            elif kind == NodeKind.ARRAY:

                self._load_array(
                    array_node=child,
                    parent_table=parent_table,
                    parent_id=parent_id,
                    model=model,
                )

    def _find_column(
        self,
        table: TableModel,
        name: str,
    ) -> ColumnModel | None:
        """
        Find a column by source/name.

        The relational mapper normally uses the document field name
        as the column name.
        """

        normalized = self._normalize_name(name)

        for column in table.columns:
            if self._normalize_name(
                column.name
            ) == normalized:
                return column

        return None

    def _find_value_column(
        self,
        table: TableModel,
    ) -> ColumnModel | None:
        """
        Find the column used to store scalar array values.

        The MVP mapper calls this column `value`.
        """

        column = self._find_column(
            table,
            "value",
        )

        if column is not None:
            return column

        # Defensive fallback:
        # choose a non-id, non-FK, non-order column.
        for candidate in table.columns:
            if candidate.primary_key:
                continue

            if candidate.name.lower() in {
                "display_order",
            }:
                continue

            return candidate

        return None

    @staticmethod
    def _find_parent_fk(
        table: TableModel,
        parent_table: TableModel,
    ) -> ForeignKeyModel | None:
        """
        Find the foreign key from child table to parent table.
        """

        for foreign_key in table.foreign_keys:
            if (
                foreign_key.referenced_table
                == parent_table.name
            ):
                return foreign_key

        return None

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:
        return value.strip().lower()

    @classmethod
    def _is_object_collection(
        cls,
        node: DocumentNode,
    ) -> bool:
        """
        Detect an object that is actually being used as a collection.

        Example:

            OBJECT
            ├── 0 OBJECT
            ├── 1 OBJECT
            └── 2 OBJECT

        This is common when JSON-like data has passed through a
        dictionary-based representation.

        We deliberately require ALL children to be:

            1. OBJECT nodes
            2. named with integer-like keys

        This avoids incorrectly treating an ordinary object such as:

            OBJECT
            ├── nutrients OBJECT
            ├── ingredients ARRAY
            └── title VALUE

        as a collection.
        """

        if not node.children:
            return False

        for index, child in enumerate(node.children):

            if cls._kind(child) != NodeKind.OBJECT:
                return False

            if child.name is None:
                return False

            try:
                child_index = int(child.name)
            except (TypeError, ValueError):
                return False

            # Optional but useful: require the keys to actually correspond
            # to their collection positions.
            if child_index != index:
                return False

        return True

    # ------------------------------------------------------------------
    # DocumentNode helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _kind(
        node: DocumentNode,
    ) -> NodeKind:
        """
        Return the NodeKind while tolerating enum/string values.
        """

        if isinstance(node.kind, NodeKind):
            return node.kind

        return NodeKind(node.kind)

    # ------------------------------------------------------------------
    # I/O functions - just call the backend
    # ------------------------------------------------------------------   
    def save_document_metadata(
        self,
        metadata: DocumentMetadata,
    ) -> None:
        return self.backend.save_document_metadata(metadata)


    def load_document_metadata(
        self,
    ) -> DocumentMetadata | None:
        return self.backend.load_document_metadata()


    def save_structure(
        self,
        model: StructureModel,
    ) -> None:
        return self.backend.save_structure(model)

    def load_structure(
        self,
    ) -> StructureModel | None:
        return self.backend.load_structure()

    def save_semantic(
        self,
        model: SemanticModel,
    ) -> None:
        return self.backend.save_semantic(model)

    def load_semantic(
        self,
    ) -> SemanticModel | None:
        return self.backend.load_semantic()

    def save_quality(
        self,
        model: QualityModel,
    ) -> None:
        return self.backend.save_quality(model)

    def load_quality(
        self,
    ) -> QualityModel | None:
        return self.backend.load_quality()
