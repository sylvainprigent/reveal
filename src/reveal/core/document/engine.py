from datetime import datetime

from reveal.core.providers.interfaces.document_provider import (
    DocumentProvider,
)
from reveal.core.providers.models.document import (
    Document,
    DocumentMetadata,
)
from reveal.core.providers.models.enums import NodeKind, SourceType
from reveal.core.providers.models.node import DocumentNode
from reveal.core.providers.models.source import Source
from reveal.core.providers.registry.content_provider import (
    ContentProviderRegistry,
)
from reveal.core.providers.registry.file_reader import (
    FileReaderRegistry,
)
from reveal.core.providers.registry.source_provider import (
    SourceProviderRegistry,
)


class DefaultDocumentProvider(DocumentProvider):
    """Build a Document from a source location.

    The provider orchestrates the three plugin layers:

    1. SourceProvider discovers the source tree.
    2. ContentProvider opens file content.
    3. FileReader parses the content into DocumentNode objects.

    The resulting Document contains only the generic data tree and
    aggregated metadata. Source and plugin implementations are not
    exposed to downstream data-analysis algorithms.
    """

    def __init__(
        self,
        source_registry: SourceProviderRegistry,
        content_registry: ContentProviderRegistry,
        reader_registry: FileReaderRegistry,
    ) -> None:
        self._source_registry = source_registry
        self._content_registry = content_registry
        self._reader_registry = reader_registry

    def load(
        self,
        location,
    ) -> Document:
        """Load a location into a Document.

        Args:
            location: Source location to load.

        Returns:
            A Document containing the complete data tree.

        Raises:
            LookupError: If no source provider supports the location.
        """
        source_provider = self._source_registry.resolve(location)
        source = source_provider.create_source(location)
        started_at = datetime.now()
        root, warnings, errors = self._load_source(source)
        duration = datetime.now() - started_at

        metadata = DocumentMetadata(
            duration=duration,
            warnings=warnings,
            errors=errors,
        )

        return Document(
            source=source,
            root=root,
            metadata=metadata,
        )

    def _load_source(
        self,
        source: Source,
    ) -> tuple[
        DocumentNode,
        list,
        list,
    ]:
        """Recursively convert a Source tree into a DocumentNode tree."""

        if source.type == SourceType.FILE:
            return self._load_file(source)

        return self._load_directory(source)

    def _load_directory(
        self,
        source: Source,
    ) -> tuple[
        DocumentNode,
        list,
        list,
    ]:
        """Recursively load all files below a source directory."""

        children: list[DocumentNode] = []
        warnings = []
        errors = []

        for child in source.children:
            node, child_warnings, child_errors = (
                self._load_source(child)
            )

            children.append(node)
            warnings.extend(child_warnings)
            errors.extend(child_errors)

        node = DocumentNode(
            kind=NodeKind.OBJECT,
            name=source.name,
            children=children,
        )

        return node, warnings, errors

    def _load_file(
        self,
        source: Source,
    ) -> tuple[
        DocumentNode,
        list,
        list,
    ]:
        """Load one file through the content and reader plugins."""

        try:
            content_provider = (
                self._content_registry.resolve(source)
            )

            content = content_provider.open(source)

            reader = self._reader_registry.resolve(source)

            result = reader.read(
                content,
                source,
            )

            return (
                result.node,
                result.warnings,
                result.errors,
            )

        except LookupError as exc:
            return (
                DocumentNode(
                    kind=NodeKind.OBJECT,
                    name=source.name,
                ),
                [],
                [str(exc)],
            )
