from pathlib import Path

from reveal.core.location.interfaces import (
    LocationResolver,
)
from reveal.core.location.models import SourceLocation


class LocalFileSystemLocationResolver(LocationResolver):
    """Resolve local filesystem paths."""

    def supports(
        self,
        value: str | Path,
    ) -> bool:
        if isinstance(value, Path):
            return True

        # URI-like values belong to other resolvers.
        return "://" not in value

    def resolve(
        self,
        value: str | Path,
    ) -> SourceLocation:
        path = Path(value).expanduser().resolve()

        return SourceLocation(
            scheme="file",
            path=str(Path(path).expanduser().resolve()),
        )


export = [
    LocalFileSystemLocationResolver,
]
