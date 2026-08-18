from abc import ABC, abstractmethod
from pathlib import Path

from reveal.core.providers.models.document import DocumentMetadata, DocumentNode
from reveal.core.quality.models import QualityModel
from reveal.core.relational.models import RelationalModel
from reveal.core.semantic.models import SemanticModel
from reveal.core.structure.models import StructureModel


class DatabaseGenerator(ABC):
    """
    Generate and populate a database from a Reveal relational model.

    A DatabaseGenerator is responsible for translating the
    database-independent RelationalModel into a concrete database
    representation and loading the corresponding DocumentNode data.
    """

    def __init__(self, location: Path) -> None:
        """
        Initialize the database generator.

        :param location: Destination of the generated database.
        """
        self.location = location

    @abstractmethod
    def create_schema(
        self,
        model: RelationalModel,
    ) -> None:
        """
        Create the database schema.

        The schema is generated from the database-independent
        RelationalModel.

        :param model: Relational schema to materialize.
        """

    @abstractmethod
    def load_data(
        self,
        root: DocumentNode,
        model: RelationalModel,
    ) -> None:
        """
        Load document data into the generated database.

        :param root: Root node of the document to load.
        :param model: Relational model describing the target schema.
        """

    @abstractmethod
    def save_metadata(
        self,
        metadata: DocumentMetadata,
    ) -> None:
        ...

    @abstractmethod
    def load_metadata(
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