from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import Field

from reveal.core.common.models import IdentifiedModel


class SourceType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"

    
class Source(IdentifiedModel):
    """Represents one input resource."""

    type: SourceType
    name: str
    path: Path
    extension: str
    mime_type: str | None = None
    encoding: str | None = None
    size: int | None = None
    sha256: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    children: list[Source] | None = None
