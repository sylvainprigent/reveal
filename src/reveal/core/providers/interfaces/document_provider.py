

from typing import Protocol
from xml.dom.minidom import Document

from reveal.core.providers.models.location import SourceLocation


class DocumentProvider(Protocol):

    def load(
        self,
        location: SourceLocation,
    ) -> Document:
        ...
