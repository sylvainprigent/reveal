from reveal.core.document.engine import DefaultDocumentProvider
from reveal.core.providers.registry.content_provider import ContentProviderRegistry
from reveal.core.providers.registry.file_reader import FileReaderRegistry
from reveal.core.providers.registry.location_resolver import LocationResolverRegistry
from reveal.core.providers.registry.source_provider import SourceProviderRegistry


class RevealRuntime:
    def __init__(self):
        self.source_registry = SourceProviderRegistry()
        self.content_registry = ContentProviderRegistry()
        self.reader_registry = FileReaderRegistry()
        self.location_registry = LocationResolverRegistry()

        self.document_provider = DefaultDocumentProvider(
            source_registry=self.source_registry,
            content_registry=self.content_registry,
            reader_registry=self.reader_registry,
        )
