from pathlib import Path

from reveal.core.interfaces.location_resolver import (
    LocationResolver,
)
from reveal.core.interfaces.registry import RegistryInterface


class LocationResolverRegistry(RegistryInterface[LocationResolver]):
    """Registry for location resolver plugins."""

    def __init__(self) -> None:
        super().__init__(
            package="reveal.plugins",
            module_name="location_resolver",
        )

    def resolve(
        self,
        value: str | Path,
    ) -> LocationResolver:
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
