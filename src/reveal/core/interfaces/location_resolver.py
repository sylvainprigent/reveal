from pathlib import Path
from typing import Protocol

from reveal.core.models.location import SourceLocation


class LocationResolver(Protocol):
    """Resolve user input into a SourceLocation."""

    def supports(
        self,
        location: str | Path,
    ) -> bool:
        """Return whether this resolver supports the location."""
        ...

    def resolve(
        self,
        location: str | Path,
    ) -> SourceLocation:
        """Convert user input into a SourceLocation."""
        ...
