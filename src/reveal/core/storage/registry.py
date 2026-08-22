from pathlib import Path

from reveal.core.common.interfaces import (
    RegistryInterface
)
from reveal.core.storage.interfaces import (
    StorageBackend
)


class StorageBackendRegistry(
    RegistryInterface[StorageBackend]
):
    """Registry for location resolver plugins."""

    def __init__(self) -> None:
        super().__init__(
            package="reveal.plugins",
            module_name="storage_backend",
        )

    def resolve(
        self,
        value: str | Path,
    ) -> StorageBackend:
        """Find the resolver supporting the given value.

        Raises:
            LookupError: If no resolver supports the value.
        """
        for resolver in self.plugins:
            if resolver.supports(value):
                return resolver

        raise LookupError(
            f"No location resolver supports: {value}"
        )