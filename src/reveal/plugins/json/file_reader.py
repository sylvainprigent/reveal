# plugins/json/reader.py

import json
from typing import Any, BinaryIO

from reveal.core.interfaces.file_reader import FileReader
from reveal.core.models.document import DocumentNode
from reveal.core.models.enums import NodeKind
from reveal.core.models.read import ReadResult
from reveal.core.models.source import Source


class JsonFileReader(FileReader):
    """Parse JSON content into a generic DocumentNode tree."""

    def supports(
        self,
        source: Source,
    ) -> bool:
        return source.extension.lower() == ".json"

    def read(
        self,
        content: BinaryIO,
        source: Source,
    ) -> ReadResult:
        try:
            data = json.load(content)

            return ReadResult(
                node=self._build_node(data)
            )

        except json.JSONDecodeError as exc:
            return ReadResult(
                node=DocumentNode(
                    kind=NodeKind.VALUE,
                    name=None,
                    value=None,
                ),
                errors=[
                    f"Invalid JSON in '{source.name}' "
                    f"at line {exc.lineno}, "
                    f"column {exc.colno}: {exc.msg}"
                ],
            )

    def _build_node(
        self,
        value: Any,
        name: str | None = None,
    ) -> DocumentNode:

        if isinstance(value, dict):
            return DocumentNode(
                kind=NodeKind.OBJECT,
                name=name,
                children=[
                    self._build_node(
                        child,
                        name=key,
                    )
                    for key, child in value.items()
                ],
            )

        if isinstance(value, list):
            return DocumentNode(
                kind=NodeKind.ARRAY,
                name=name,
                children=[
                    self._build_node(
                        child,
                        name=str(index),
                    )
                    for index, child in enumerate(value)
                ],
            )

        return DocumentNode(
            kind=NodeKind.VALUE,
            name=name,
            value=value,
        )

export = [JsonFileReader]
