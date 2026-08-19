from typing import Protocol
from xml.dom.minidom import Document

from reveal.core.location.models import SourceLocation


class DocumentProvider(Protocol):

    def load(
        self,
        location: SourceLocation,
    ) -> Document:
        ...
