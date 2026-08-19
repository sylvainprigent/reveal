from typing import BinaryIO, Protocol

from reveal.core.filereader.models import ReadResult
from reveal.core.source.models import Source


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
