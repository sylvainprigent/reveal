from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from reveal.core.document.models import DocumentMetadata
from reveal.core.quality.models import QualityModel
from reveal.core.relational.models import ColumnNullability, RelationalType
from reveal.core.semantic.models import SemanticModel
from reveal.core.storage.interfaces import StorageBackend
from reveal.core.storage.models import StorageColumn, StorageForeignKey
from reveal.core.structure.models import StructureModel


class SQLiteBackend(StorageBackend):

    def __init__(self, location: Path | None = None):
        if location is not None:
            self.location = Path(location)
        self.connection: sqlite3.Connection | None = None

    def supports(self, value: str | Path) -> bool:
        path = Path(value)
        self.location = path

        print("PATH RESOLVE LOWER = ", path.suffix.lower())
        if path.suffix.lower() in {".sqlite", ".sqlite3"}:
            return True

        if path.suffix.lower() == ".db":
            # If the file des not exists, I will create a sqlite storage
            if not path.is_file():
                return True
            # otherwise, I check the header
            return self.is_sqlite_database(path)

        return False

    def is_sqlite_database(path: str | Path) -> bool:
        """Return True if the file appears to be a SQLite database."""
        path = Path(path)

        try:
            with path.open("rb") as f:
                header = f.read(16)

            return header == b"SQLite format 3\x00"

        except (OSError, PermissionError):
            return False

    def open(self) -> None:
        self.location.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connection = sqlite3.connect(
            self.location
        )

        self.connection.execute(
            "PRAGMA foreign_keys = ON"
        )

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def create_table(
        self,
        name: str,
        columns: list[StorageColumn],
        foreign_keys: list[StorageForeignKey],
    ) -> None:

        column_definitions: list[str] = []

        for column in columns:
            column_definitions.append(
                self._column_definition(column)
            )

        for foreign_key in foreign_keys:
            column_definitions.append(
                self._foreign_key_definition(foreign_key)
            )

        sql = (
            f'CREATE TABLE IF NOT EXISTS '
            f'"{self._quote_identifier(name)}" '
            f"(\n"
            + ",\n".join(
                f"    {definition}"
                for definition in column_definitions
            )
            + "\n)"
        )

        self.connection.execute(sql)


    def _column_definition(
        self,
        column: StorageColumn,
    ) -> str:
        parts = [
            f'"{self._quote_identifier(column.name)}"',
            self._sqlite_type(column.type),
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
        foreign_key: StorageForeignKey,
    ) -> str:
        return (
            f'FOREIGN KEY '
            f'("{self._quote_identifier(foreign_key.column)}") '
            f'REFERENCES '
            f'"{self._quote_identifier(foreign_key.referenced_table)}"'
            f'("{self._quote_identifier(foreign_key.referenced_column)}")'
        )
    
    def insert(
        self,
        table: str,
        values: dict[str, Any],
    ) -> int:

        if not values:
            sql = (
                f'INSERT INTO '
                f'"{self._quote_identifier(table)}" '
                f"DEFAULT VALUES"
            )
            cursor = self.connection.execute(sql)
        else:
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
                f'"{self._quote_identifier(table)}" '
                f"({quoted_columns}) "
                f"VALUES ({placeholders})"
            )

            cursor = self.connection.execute(
                sql,
                [
                    values[column]
                    for column in columns
                ],
            )

        return int(cursor.lastrowid)

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()


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
    # metadata, 
    # ------------------------------------------------------------------
    @staticmethod
    def _ensure_database(
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reveal_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reveal_analysis (
                analysis_type TEXT PRIMARY KEY,
                version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )

    def save_document_metadata(
        self,
        metadata: DocumentMetadata,
    ) -> None:

        payload = metadata.model_dump_json()

        with sqlite3.connect(self.location) as connection:
            self._ensure_database(connection)
            connection.execute(
                """
                INSERT INTO reveal_metadata (
                    key,
                    value
                )
                VALUES (?, ?)
                ON CONFLICT(key)
                DO UPDATE SET
                    value = excluded.value
                """,
                (
                    "document",
                    payload,
                ),
            )

            connection.commit()


    def load_document_metadata(
        self,
    ) -> DocumentMetadata | None:

        with sqlite3.connect(self.location) as connection:
            self._ensure_database(connection)
            row = connection.execute(
                """
                SELECT value
                FROM reveal_metadata
                WHERE key = ?
                """,
                ("document",),
            ).fetchone()

        if row is None:
            return None

        return DocumentMetadata.model_validate_json(
            row[0]
        )


    def _save_analysis(
        self,
        analysis_type: str,
        model: Any,
    ) -> None:

        payload = model.model_dump_json()

        created_at = datetime.now(
            timezone.utc
        ).isoformat()

        with sqlite3.connect(self.location) as connection:
            self._ensure_database(connection)
            connection.execute(
                """
                INSERT INTO reveal_analysis (
                    analysis_type,
                    version,
                    created_at,
                    payload
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(analysis_type)
                DO UPDATE SET
                    version = excluded.version,
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (
                    analysis_type,
                    1,
                    created_at,
                    payload,
                ),
            )

            connection.commit()

    def _load_analysis(
        self,
        analysis_type: str,
        model_type: type[Any],
    ) -> Any | None:

        with sqlite3.connect(self.location) as connection:
            self._ensure_database(connection)
            row = connection.execute(
                """
                SELECT payload
                FROM reveal_analysis
                WHERE analysis_type = ?
                """,
                (analysis_type,),
            ).fetchone()

        if row is None:
            return None

        return model_type.model_validate_json(
            row[0]
        )

    def save_structure(
        self,
        model: StructureModel,
    ) -> None:
        self._save_analysis(
            analysis_type="structure",
            model=model,
        )

    def load_structure(
        self,
    ) -> StructureModel | None:
        return self._load_analysis(
            analysis_type="structure",
            model_type=StructureModel,
        )

    def save_semantic(
        self,
        model: SemanticModel,
    ) -> None:
        self._save_analysis(
            analysis_type="semantic",
            model=model,
        )

    def load_semantic(
        self,
    ) -> SemanticModel | None:
        return self._load_analysis(
            analysis_type="semantic",
            model_type=SemanticModel,
        )

    def save_quality(
        self,
        model: QualityModel,
    ) -> None:
        self._save_analysis(
            analysis_type="quality",
            model=model,
        )

    def load_quality(
        self,
    ) -> QualityModel | None:
        return self._load_analysis(
            analysis_type="quality",
            model_type=QualityModel,
        )


export = [SQLiteBackend]
