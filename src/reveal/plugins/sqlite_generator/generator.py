from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from reveal.core.providers.models.enums import NodeKind
from reveal.core.providers.models.document import DocumentNode
from reveal.core.relational.models import (
    ColumnModel,
    ColumnNullability,
    ForeignKeyModel,
    RelationalModel,
    RelationalType,
    TableModel,
)


class SQLiteDatabaseGenerator:
    """
    SQLite implementation of the database generator.

    The generator is deliberately based on the database-independent
    RelationalModel. It does not make assumptions about the database
    schema beyond SQLite-specific SQL syntax.

    Data loading is performed recursively from a DocumentNode tree.
    """

    def __init__(self, location: Path) -> None:
        self.location = Path(location)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_schema(
        self,
        model: RelationalModel,
    ) -> None:
        """
        Create the SQLite database schema from a RelationalModel.
        """

        self.location.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.location) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            for table in model.tables:
                self._create_table(
                    connection,
                    table,
                )

            connection.commit()

    def load_data(
        self,
        root: DocumentNode,
        model: RelationalModel,
    ) -> None:
        """
        Load a DocumentNode tree into the SQLite database.

        The algorithm recursively follows the same structure used by
        the RelationalMapper.
        """

        if not self.location.exists():
            raise FileNotFoundError(
                f"SQLite database does not exist: {self.location}"
            )

        with sqlite3.connect(self.location) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            # Start from the document table.
            document_table = self._find_document_table(model)

            self._load_root(
                connection=connection,
                root=root,
                table=document_table,
                model=model,
            )

            connection.commit()

    # ------------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------------

    def _create_table(
        self,
        connection: sqlite3.Connection,
        table: TableModel,
    ) -> None:
        column_definitions: list[str] = []

        for column in table.columns:
            column_definitions.append(
                self._column_definition(column)
            )

        for foreign_key in table.foreign_keys:
            column_definitions.append(
                self._foreign_key_definition(foreign_key)
            )

        sql = (
            f'CREATE TABLE IF NOT EXISTS '
            f'"{self._quote_identifier(table.name)}" '
            f"(\n"
            + ",\n".join(
                f"    {definition}"
                for definition in column_definitions
            )
            + "\n)"
        )

        connection.execute(sql)

    def _column_definition(
        self,
        column: ColumnModel,
    ) -> str:
        parts = [
            f'"{self._quote_identifier(column.name)}"',
            self._sqlite_type(column.relational_type),
        ]

        if column.primary_key:
            parts.append("PRIMARY KEY")

        if (
            column.nullable == ColumnNullability.REQUIRED
            and not column.primary_key
        ):
            parts.append("NOT NULL")

        if column.unique:
            parts.append("UNIQUE")

        return " ".join(parts)

    def _foreign_key_definition(
        self,
        foreign_key: ForeignKeyModel,
    ) -> str:
        return (
            f'FOREIGN KEY '
            f'("{self._quote_identifier(foreign_key.column)}") '
            f'REFERENCES '
            f'"{self._quote_identifier(foreign_key.referenced_table)}"'
            f'("{self._quote_identifier(foreign_key.referenced_column)}")'
        )

    @staticmethod
    def _sqlite_type(
        relational_type: RelationalType | str,
    ) -> str:
        if isinstance(relational_type, RelationalType):
            value = relational_type.value
        else:
            value = relational_type

        mapping = {
            "boolean": "INTEGER",
            "integer": "INTEGER",
            "float": "REAL",
            "decimal": "REAL",
            "string": "TEXT",
            "text": "TEXT",
            "date": "TEXT",
            "datetime": "TEXT",
            "time": "TEXT",
            "json": "TEXT",
            "binary": "BLOB",
        }

        return mapping.get(
            value,
            "TEXT",
        )

    # ------------------------------------------------------------------
    # Root loading
    # ------------------------------------------------------------------

    def _load_root(
        self,
        connection: sqlite3.Connection,
        root: DocumentNode,
        table: TableModel,
        model: RelationalModel,
    ) -> None:
        """
        Load the document root.

        Reveal can represent a collection of records in two ways:

            ARRAY
                -> OBJECT
                -> OBJECT
                -> ...

        or, depending on the source parser:

            OBJECT
                -> "0" OBJECT
                -> "1" OBJECT
                -> "2" OBJECT
                -> ...

        The second form is treated as a collection when all children
        are OBJECT nodes with numeric names.
        """

        kind = self._kind(root)

        # --------------------------------------------------------------
        # Explicit ARRAY root
        # --------------------------------------------------------------

        if kind == NodeKind.ARRAY:
            for index, child in enumerate(root.children):
                if self._kind(child) != NodeKind.OBJECT:
                    continue

                self._load_object(
                    connection=connection,
                    node=child,
                    table=table,
                    model=model,
                    parent_table=None,
                    parent_id=None,
                    display_order=index,
                )

            return

        # --------------------------------------------------------------
        # OBJECT root
        #
        # It may actually represent a collection:
        #
        # OBJECT
        # ├── 0 OBJECT
        # ├── 1 OBJECT
        # └── 2 OBJECT
        # --------------------------------------------------------------

        if kind == NodeKind.OBJECT:

            if self._is_object_collection(root):
                for index, child in enumerate(root.children):

                    self._load_object(
                        connection=connection,
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
                connection=connection,
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

    # ------------------------------------------------------------------
    # Recursive object loading
    # ------------------------------------------------------------------

    def _load_object(
        self,
        connection: sqlite3.Connection,
        node: DocumentNode,
        table: TableModel,
        model: RelationalModel,
        parent_table: TableModel | None,
        parent_id: int | None,
        display_order: int | None,
    ) -> int:
        """
        Insert one object into one relational table.

        Returns the generated primary key.
        """

        values: dict[str, Any] = {}

        # --------------------------------------------------------------
        # Parent foreign key
        # --------------------------------------------------------------

        if parent_table is not None and parent_id is not None:
            fk = self._find_parent_fk(
                table=table,
                parent_table=parent_table,
            )

            if fk is not None:
                values[fk.column] = parent_id

        # --------------------------------------------------------------
        # Display order
        # --------------------------------------------------------------

        if display_order is not None:
            display_order_column = self._find_column(
                table,
                "display_order",
            )

            if display_order_column is not None:
                values[
                    display_order_column.name
                ] = display_order

        # --------------------------------------------------------------
        # Scalar fields
        # --------------------------------------------------------------

        for child in node.children:
            if self._kind(child) != NodeKind.VALUE:
                continue

            if child.name is None:
                continue

            column = self._find_column(
                table,
                child.name,
            )

            if column is None:
                continue

            values[column.name] = child.value

        # --------------------------------------------------------------
        # Insert
        # --------------------------------------------------------------

        row_id = self._insert_row(
            connection=connection,
            table=table,
            values=values,
        )

        # --------------------------------------------------------------
        # Recursive children
        # --------------------------------------------------------------

        self._load_children(
            connection=connection,
            node=node,
            parent_table=table,
            parent_id=row_id,
            model=model,
        )

        return row_id

    # ------------------------------------------------------------------
    # Child loading
    # ------------------------------------------------------------------

    def _load_children(
        self,
        connection: sqlite3.Connection,
        node: DocumentNode,
        parent_table: TableModel,
        parent_id: int,
        model: RelationalModel,
    ) -> None:
        """
        Recursively load OBJECT and ARRAY children.
        """

        for child in node.children:
            if child.name is None:
                continue

            kind = self._kind(child)

            # ----------------------------------------------------------
            # OBJECT child
            # ----------------------------------------------------------

            if kind == NodeKind.OBJECT:
                child_table = self._find_child_table(
                    model=model,
                    parent_table=parent_table,
                    child_name=child.name,
                )

                if child_table is None:
                    continue

                self._load_object(
                    connection=connection,
                    node=child,
                    table=child_table,
                    model=model,
                    parent_table=parent_table,
                    parent_id=parent_id,
                    display_order=None,
                )

            # ----------------------------------------------------------
            # ARRAY child
            # ----------------------------------------------------------

            elif kind == NodeKind.ARRAY:
                self._load_array(
                    connection=connection,
                    array_node=child,
                    parent_table=parent_table,
                    parent_id=parent_id,
                    model=model,
                )

    # ------------------------------------------------------------------
    # Array loading
    # ------------------------------------------------------------------

    def _load_array(
        self,
        connection: sqlite3.Connection,
        array_node: DocumentNode,
        parent_table: TableModel,
        parent_id: int,
        model: RelationalModel,
    ) -> None:
        """
        Load an ARRAY into its child table.

        Each array element becomes one row.

        Scalar element:

            ingredients[]
                -> value
                -> display_order
                -> parent FK

        Object element:

            ingredients[]
                -> object fields
                -> display_order
                -> parent FK
        """

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
            kind = self._kind(element)

            # ----------------------------------------------------------
            # Scalar array element
            # ----------------------------------------------------------

            if kind == NodeKind.VALUE:
                values: dict[str, Any] = {}

                fk = self._find_parent_fk(
                    table=child_table,
                    parent_table=parent_table,
                )

                if fk is not None:
                    values[fk.column] = parent_id

                value_column = self._find_value_column(
                    child_table,
                )

                if value_column is not None:
                    values[
                        value_column.name
                    ] = element.value

                order_column = self._find_column(
                    child_table,
                    "display_order",
                )

                if order_column is not None:
                    values[
                        order_column.name
                    ] = index

                self._insert_row(
                    connection=connection,
                    table=child_table,
                    values=values,
                )

                continue

            # ----------------------------------------------------------
            # Object array element
            # ----------------------------------------------------------

            if kind == NodeKind.OBJECT:
                self._load_object(
                    connection=connection,
                    node=element,
                    table=child_table,
                    model=model,
                    parent_table=parent_table,
                    parent_id=parent_id,
                    display_order=index,
                )

    # ------------------------------------------------------------------
    # SQL INSERT
    # ------------------------------------------------------------------

    def _insert_row(
        self,
        connection: sqlite3.Connection,
        table: TableModel,
        values: dict[str, Any],
    ) -> int:
        """
        Insert one row and return its generated ID.

        Only columns actually present in `values` are inserted.
        SQLite therefore handles nullable columns naturally.
        """

        if not values:
            sql = (
                f'INSERT INTO '
                f'"{self._quote_identifier(table.name)}" '
                f"DEFAULT VALUES"
            )

            cursor = connection.execute(sql)
            return int(cursor.lastrowid)

        columns = list(values.keys())

        quoted_columns = ", ".join(
            f'"{self._quote_identifier(column)}"'
            for column in columns
        )

        placeholders = ", ".join(
            "?" for _ in columns
        )

        sql = (
            f'INSERT INTO '
            f'"{self._quote_identifier(table.name)}" '
            f"({quoted_columns}) "
            f"VALUES ({placeholders})"
        )

        cursor = connection.execute(
            sql,
            [
                values[column]
                for column in columns
            ],
        )

        return int(cursor.lastrowid)

    # ------------------------------------------------------------------
    # Model lookup
    # ------------------------------------------------------------------

    def _find_document_table(
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
    # Naming / identifiers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:
        return value.strip().lower()

    @staticmethod
    def _quote_identifier(
        value: str,
    ) -> str:
        """
        Escape a SQLite identifier.

        Double quotes inside an identifier are represented
        by two double quotes.
        """

        return value.replace(
            '"',
            '""',
        )

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