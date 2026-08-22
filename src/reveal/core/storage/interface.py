from abc import ABC, abstractmethod
from typing import Any

from reveal.core.document.models import DocumentMetadata
from reveal.core.quality.models import QualityModel
from reveal.core.semantic.models import SemanticModel
from reveal.core.structure.models import StructureModel

from reveal.core.storage.models import (
    StorageColumn,
    StorageForeignKey
)


class StorageBackend(ABC):
    """
    Database-independent storage backend.

    The DatabaseGenerator owns the persistence algorithm.
    A backend only translates generic storage instructions
    into its concrete storage technology.
    """

    @abstractmethod
    def open(self) -> None:
        """Open or initialize the storage."""

    @abstractmethod
    def close(self) -> None:
        """Close the storage."""

    @abstractmethod
    def create_table(
        self,
        name: str,
        columns: list[StorageColumn],
        foreign_keys: list[StorageForeignKey],
    ) -> None:
        """Create a table/collection in the storage."""

    @abstractmethod
    def insert(
        self,
        table: str,
        values: dict[str, Any],
    ) -> Any:
        """
        Insert one record.

        Returns the generated identifier of the record.
        """

    @abstractmethod
    def save_document_metadata(
        self,
        metadata: DocumentMetadata,
    ) -> None:
        ...

    @abstractmethod
    def load_document_metadata(
        self,
    ) -> DocumentMetadata | None:
        ...

    @abstractmethod
    def save_structure(
        self,
        model: StructureModel,
    ) -> None:
        ...

    @abstractmethod
    def load_structure(
        self,
    ) -> StructureModel | None:
        ...

    @abstractmethod
    def save_semantic(
        self,
        model: SemanticModel,
    ) -> None:
        ...

    @abstractmethod
    def load_semantic(
        self,
    ) -> SemanticModel | None:
        ...

    @abstractmethod
    def save_quality(
        self,
        model: QualityModel,
    ) -> None:
        ...

    @abstractmethod
    def load_quality(
        self,
    ) -> QualityModel | None:
        ...

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
