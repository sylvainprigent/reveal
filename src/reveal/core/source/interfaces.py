from typing import Protocol

from reveal.core.location.models import SourceLocation
from reveal.core.source.models import Source


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
