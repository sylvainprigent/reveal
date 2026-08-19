from __future__ import annotations

from datetime import timedelta

from pydantic import Field

from reveal.core.content.models import DocumentNode
from reveal.core.filereader.models import ReadError, ReadWarning

from reveal.core.common.models import CoreModel, IdentifiedModel
from reveal.core.source.models import Source


class DocumentMetadata(CoreModel):
    duration: timedelta | None = None

    warnings: list[ReadWarning] = Field(default_factory=list)
    errors: list[ReadError] = Field(default_factory=list)


class Document(IdentifiedModel):
    """
    Immutable in-memory representation of a document.

    The root field stores the original parsed structure
    exactly as returned by the reader plugin.
    """
    source: Source
    root: DocumentNode #This actually contains the loaded data
    metadata: DocumentMetadata
