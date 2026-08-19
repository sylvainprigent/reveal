from reveal.core.common.interfaces import RegistryInterface
from reveal.core.source.interfaces import SourceProvider
from reveal.core.location.models import SourceLocation


class SourceProviderRegistry(
    RegistryInterface[SourceProvider]
):
    def __init__(self) -> None:
        super().__init__(
            package="reveal.plugins",
            module_name="source_provider",
        )

    def resolve(
        self,
        location: SourceLocation,
    ) -> SourceProvider:
        for provider in self._plugins:
            if provider.supports(location):
                return provider

        raise LookupError(
            f"No source provider supports: {location}"
        )

    @property
    def plugins(self) -> tuple[SourceProvider, ...]:
        """Return all discovered readers."""
        return tuple(self.plugins)
