from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class CoreModel(BaseModel):
    """Base immutable model for every domain object."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False,
        use_enum_values=True,
    )


class IdentifiedModel(CoreModel):
    """Base model with a generated UUID."""

    id: UUID = Field(default_factory=uuid4)
