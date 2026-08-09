from pathlib import Path

from reveal.core.models.location import SourceLocation


class Location:
    @staticmethod
    def from_path(
        path: str | Path,
    ) -> SourceLocation:
        return SourceLocation(
            scheme="file",
            path=str(Path(path).expanduser().resolve()),
        )
