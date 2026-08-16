from __future__ import annotations

from pathlib import Path
from uuid import UUID

from pydantic import Field

from .common import CoreModel


class Provenance(CoreModel):
    """Origin of a piece of data."""

    source_id: UUID
    document_path: str
    sheet_name: str | None = None
    row: int | None = None
    column: int | str | None = None
    byte_offset: int | None = None
    file_path: Path | None = None