from reveal.core.common.interfaces import RegistryInterface
from reveal.core.filereader.interfaces import FileReader
from reveal.core.source.models import Source


class FileReaderRegistry(
    RegistryInterface[FileReader]
):
    def __init__(self) -> None:
        super().__init__(
            package="reveal.plugins",
            module_name="file_reader",
        )

    def resolve(
        self,
        source: Source,
    ) -> FileReader:
        for reader in self._plugins:
            if reader.supports(source):
                return reader

        raise LookupError(
            f"No file reader supports source: "
            f"{source.name}"
        )

    @property
    def plugins(self) -> tuple[FileReader, ...]:
        """Return all discovered readers."""
        return tuple(self._plugins)
