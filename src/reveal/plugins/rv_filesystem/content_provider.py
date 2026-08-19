# plugins/filesystem/content_provider.py

from pathlib import Path
from typing import BinaryIO

from reveal.core.content.interfaces import ContentProvider
from reveal.core.source.models import SourceType, Source


class LocalFileSystemContentProvider(ContentProvider):
    """Provides binary access to files on the local filesystem."""

    def supports(
        self,
        source: Source,
    ) -> bool:
        return (
            source.type == SourceType.FILE
            and source.path is not None
        )

    def open(
        self,
        source: Source,
    ) -> BinaryIO:
        if not self.supports(source):
            raise ValueError(
                f"Source is not a supported local file: "
                f"{source.path}"
            )

        path = Path(source.path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Expected a file: {path}"
            )

        return path.open("rb")


export = [LocalFileSystemContentProvider]
