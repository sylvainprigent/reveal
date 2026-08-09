from reveal.core.interfaces.registry import RegistryInterface
from reveal.core.interfaces.content_provider import ContentProvider
from reveal.core.models.source import Source


class ContentProviderRegistry(
    RegistryInterface[ContentProvider]
):
    def __init__(self) -> None:
        super().__init__(
            package="reveal.plugins",
            module_name="content_provider",
        )

    def resolve(
        self,
        source: Source,
    ) -> ContentProvider:
        for provider in self._plugins:
            if provider.supports(source):
                return provider

        raise LookupError(
            f"No file reader supports source: "
            f"{source.name}"
        )

    @property
    def plugins(self) -> tuple[ContentProvider, ...]:
        """Return all discovered providers."""
        return tuple(self._plugins)
