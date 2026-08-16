from typing import BinaryIO
from uuid import UUID

from pydantic import Field

from reveal.core.providers.models.common import CoreModel
from reveal.core.providers.models.node import DocumentNode


class ReadResult(CoreModel):
    node: DocumentNode
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ReadDiagnostic(CoreModel):
    source_id: UUID
    message: str
    path: str | None = None
    details: str | None = None


class ReadWarning(ReadDiagnostic):
    pass


class ReadError(ReadDiagnostic):
    pass
