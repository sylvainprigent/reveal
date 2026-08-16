from typing import Protocol

from reveal.core.providers.models.location import SourceLocation
from reveal.core.providers.models.source import Source


class SourceProvider(Protocol):

    def supports(
        self,
        location: SourceLocation,
    ) -> bool:
        ...

    def create_source(
        self,
        location: SourceLocation,
    ) -> Source:
        ...
