

from typing import Any

from pydantic import Field

from reveal.core.models.common import CoreModel


class SourceLocation(CoreModel):
    scheme: str
    path: str
    options: dict[str, Any] = Field(default_factory=dict)
