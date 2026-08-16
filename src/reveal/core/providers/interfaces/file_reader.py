from typing import BinaryIO, Protocol

from reveal.core.providers.models.read import ReadResult
from reveal.core.providers.models.source import Source


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