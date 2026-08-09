from reveal.core.providers.document import DefaultDocumentProvider
from reveal.core.registry.content_provider import ContentProviderRegistry
from reveal.core.registry.file_reader import FileReaderRegistry
from reveal.core.registry.location_resolver import LocationResolverRegistry
from reveal.core.registry.source_provider import SourceProviderRegistry


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
