from typing import BinaryIO, Protocol

from reveal.core.models.source import Source


class ContentProvider(Protocol):

    def supports(
        self,
        source: Source,
    ) -> bool:
        ...

    def open(
        self,
        source: Source,
    ) -> BinaryIO:
        ...
