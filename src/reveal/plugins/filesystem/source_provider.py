# plugins/filesystem/provider.py

from pathlib import Path
import hashlib
import mimetypes
from datetime import datetime

from reveal.core.providers.models.location import SourceLocation
from reveal.core.providers.models.source import Source
from reveal.core.providers.models.enums import SourceType
from reveal.core.providers.interfaces.source_provider import SourceProvider


class LocalFileSystemSourceProvider(SourceProvider):
    """
    Source provider for local filesystem resources.
    Supports files and recursive directories.
    """

    def __init__(
        self,
        compute_hash: bool = True,
    ):
        self.compute_hash = compute_hash

    def supports(
        self,
        location: SourceLocation,
    ) -> bool:
        return location.scheme == "file"

    def create_source(
        self,
        location: SourceLocation,
    ) -> Source:

        path = Path(location.path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(
                f"Source not found: {path}"
            )

        if path.is_dir():
            return self._create_directory_source(path)

        return self._create_file_source(path)

    def _create_directory_source(
        self,
        path: Path,
    ) -> Source:

        stat = path.stat()

        children = [
            self.create_source(child)
            for child in sorted(path.iterdir())
        ]

        return Source(
            type=SourceType.DIRECTORY,
            name=path.name,
            path=path,
            extension=None,
            mime_type=None,
            encoding=None,
            size=None,
            sha256=None,
            created_at=datetime.fromtimestamp(
                stat.st_ctime
            ),
            modified_at=datetime.fromtimestamp(
                stat.st_mtime
            ),
            children=children,
        )

    def _create_file_source(
        self,
        path: Path,
    ) -> Source:

        stat = path.stat()

        mime_type, _ = mimetypes.guess_type(
            path.name
        )

        return Source(
            type=SourceType.FILE,
            name=path.name,
            path=path,
            extension=path.suffix.lower(),
            mime_type=mime_type,
            encoding=None,
            size=stat.st_size,
            sha256=(
                self._hash_file(path)
                if self.compute_hash
                else None
            ),
            created_at=datetime.fromtimestamp(
                stat.st_ctime
            ),
            modified_at=datetime.fromtimestamp(
                stat.st_mtime
            ),
            children=[],
        )

    @staticmethod
    def _hash_file(
        path: Path,
        chunk_size: int = 1024 * 1024,
    ) -> str:

        sha256 = hashlib.sha256()

        with path.open("rb") as file:
            while chunk := file.read(chunk_size):
                sha256.update(chunk)

        return sha256.hexdigest()


export = [LocalFileSystemSourceProvider]