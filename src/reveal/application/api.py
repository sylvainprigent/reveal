from pathlib import Path

from reveal.application.runtime import RevealRuntime
from reveal.core.providers.models.document import Document
from reveal.core.providers.models.location import SourceLocation


_runtime = RevealRuntime()


def load(
    input: str | Path | SourceLocation,
) -> Document:
    if isinstance(input, SourceLocation):
        location = input
    else:
        resolver = _runtime.location_registry.resolve(input)
        location = resolver.resolve(input)

    return _runtime.document_provider.load(location)


def inspect(document: Document):
    ...


def export(document, destination):
    ...