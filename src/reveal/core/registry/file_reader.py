from reveal.core.interfaces.registry import RegistryInterface
from reveal.core.interfaces.file_reader import FileReader
from reveal.core.models.source import Source


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
