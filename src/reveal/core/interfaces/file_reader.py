from typing import BinaryIO, Protocol

from reveal.core.models.read import ReadResult
from reveal.core.models.source import Source
from reveal.core.models.document import Document


class FileReader(Protocol):

    def supports(
        self,
        source: Source,
    ) -> bool:
        ...

    def read(
        self,
        content: BinaryIO,
        source: Source,
    ) -> ReadResult:
        ...