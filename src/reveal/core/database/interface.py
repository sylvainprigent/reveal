from abc import ABC, abstractmethod
from pathlib import Path

from reveal.core.providers.models.document import DocumentNode
from reveal.core.relational.models import RelationalModel


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
