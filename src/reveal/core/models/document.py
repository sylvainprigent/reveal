from __future__ import annotations

from datetime import timedelta
from enum import Enum
from typing import Any

from pydantic import Field

from reveal.core.models.node import DocumentNode
from reveal.core.models.read import ReadError, ReadWarning

from .common import CoreModel, IdentifiedModel
from .source import Source


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